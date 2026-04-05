"""Service de création de partie : bibliothèques, pioche, mulligan, premier tour."""

from __future__ import annotations

import random

from baobab_mtg_rules_engine.catalog.card_definition_port import CardDefinitionPort
from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game import Game
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.setup.deck_definition import DeckDefinition
from baobab_mtg_rules_engine.setup.deck_validator import DeckValidator
from baobab_mtg_rules_engine.setup.game_setup_request import GameSetupRequest
from baobab_mtg_rules_engine.setup.mulligan_choice_port import MulliganChoicePort
from baobab_mtg_rules_engine.setup.mulligan_policy import MulliganPolicy


class GameFactory:
    """Construit une :class:`Game` jouable à partir de decks validés et d'une graine.

    :param catalog: Port catalogue pour la validation des clés.
    :param mulligan_policy: Politique documentée ; défaut :class:`MulliganPolicy`.
    """

    def __init__(
        self,
        catalog: CardDefinitionPort,
        *,
        mulligan_policy: MulliganPolicy | None = None,
    ) -> None:
        self._catalog: CardDefinitionPort = catalog
        self._mulligan_policy: MulliganPolicy = mulligan_policy or MulliganPolicy()

    def create_game(
        self,
        request: GameSetupRequest,
        mulligan_choice: MulliganChoicePort,
    ) -> Game:
        """Crée une partie deux joueurs avec setup complet et journal d'événements.

        :param request: Paramètres déterministes et decks.
        :param mulligan_choice: Décisions de mulligan injectées depuis l'extérieur.
        :return: Partie prête avec tour initial positionné sur le joueur qui commence.
        """
        validator = DeckValidator(self._catalog)
        validator.validate(request.decks[0])
        validator.validate(request.decks[1])

        # PRNG déterministe pour rejouabilité (hors usage cryptographique).
        rng = random.Random(request.rng_seed)  # nosec B311
        state = GameState.new_two_player(names=request.player_names)
        state.record_engine_event(
            EventType.SETUP_DECKS_VALIDATED,
            (("rng_seed", request.rng_seed),),
        )

        self._build_library(state, 0, request.decks[0])
        state.record_engine_event(
            EventType.SETUP_LIBRARY_BUILT,
            (
                ("player_index", 0),
                ("card_count", request.decks[0].total_cards()),
            ),
        )
        self._build_library(state, 1, request.decks[1])
        state.record_engine_event(
            EventType.SETUP_LIBRARY_BUILT,
            (
                ("player_index", 1),
                ("card_count", request.decks[1].total_cards()),
            ),
        )

        state.shuffle_player_library(0, rng)
        state.record_engine_event(EventType.SETUP_LIBRARY_SHUFFLED, (("player_index", 0),))
        state.shuffle_player_library(1, rng)
        state.record_engine_event(EventType.SETUP_LIBRARY_SHUFFLED, (("player_index", 1),))

        starting_player = (
            request.starting_player
            if request.starting_player is not None
            else int(rng.randrange(2))
        )
        state.replace_turn_state(TurnState.start_first_turn(starting_player))
        state.record_engine_event(
            EventType.SETUP_STARTING_PLAYER_DETERMINED,
            (("starting_player", starting_player),),
        )

        for player_index in (0, 1):
            drawn = state.draw_cards_from_library_to_hand(
                player_index,
                self._mulligan_policy.OPENING_HAND,
            )
            state.record_engine_event(
                EventType.SETUP_OPENING_HAND_DRAWN,
                (
                    ("player_index", player_index),
                    ("count", len(drawn)),
                ),
            )

        self._resolve_mulligans(state, starting_player, rng, mulligan_choice)

        state.record_engine_event(
            EventType.SETUP_FIRST_TURN_READY,
            (("active_player", starting_player),),
        )
        return Game(game_id=request.game_id, state=state)

    def _build_library(self, state: GameState, player_index: int, deck: DeckDefinition) -> None:
        location = ZoneLocation(player_index, ZoneType.LIBRARY)
        for catalog_key in deck.sorted_expansion_keys():
            object_id = state.issue_object_id()
            card = InGameCard(object_id, CardReference(catalog_key))
            state.register_object_at(card, location)

    def _resolve_mulligans(
        self,
        state: GameState,
        starting_player: int,
        rng: random.Random,
        choice: MulliganChoicePort,
    ) -> None:
        resolution_order = (starting_player, 1 - starting_player)
        mulligan_counts = [0, 0]
        for player_index in resolution_order:
            while True:
                hand_zone = state.players[player_index].zone(ZoneType.HAND)
                hand_ids = hand_zone.object_ids()
                depth = mulligan_counts[player_index]
                if not choice.should_take_mulligan(
                    player_index,
                    mulligan_depth=depth,
                    hand_object_ids=hand_ids,
                ):
                    break
                library_location = ZoneLocation(player_index, ZoneType.LIBRARY)
                for object_id in list(hand_ids):
                    state.relocate_preserving_identity(object_id, library_location)
                state.shuffle_player_library(player_index, rng)
                mulligan_counts[player_index] += 1
                next_size = self._mulligan_policy.hand_size_after_mulligans(
                    mulligan_counts[player_index],
                )
                drawn = state.draw_cards_from_library_to_hand(player_index, next_size)
                state.record_engine_event(
                    EventType.SETUP_MULLIGAN_TAKEN,
                    (
                        ("player_index", player_index),
                        ("mulligan_count", mulligan_counts[player_index]),
                        ("drawn", len(drawn)),
                    ),
                )
