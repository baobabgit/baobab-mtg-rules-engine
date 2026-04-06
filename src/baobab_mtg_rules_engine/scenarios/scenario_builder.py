"""Construction déterministe de petits états de partie pour tests et scénarios."""

from __future__ import annotations

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.engine.legal_action_service import LegalActionService
from baobab_mtg_rules_engine.engine.turn_manager import TurnManager
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError
from baobab_mtg_rules_engine.scenarios.scenario_context import ScenarioContext


class ScenarioBuilder:
    """Chaîne de configuration jusqu'à un :class:`ScenarioContext` figé et rejouable.

    Les cartes et permanents enregistrés avec un **alias** peuvent être visés par
    :class:`~baobab_mtg_rules_engine.replay.recorded_game_action.RecordedGameAction`.

    :param rules: Port gameplay utilisé pour les actions légales et le ``TurnManager``.
    """

    def __init__(self, rules: CardGameplayPort) -> None:
        self._rules: CardGameplayPort = rules
        self._state: GameState | None = None
        self._aliases: dict[str, GameObjectId] = {}

    def with_two_player_game(
        self,
        *,
        names: tuple[str, str] | None = None,
        life_totals: tuple[int, int] | None = None,
    ) -> ScenarioBuilder:
        """Initialise un duel standard (cf. :meth:`GameState.new_two_player`)."""
        self._state = GameState.new_two_player(names=names, life_totals=life_totals)
        self._aliases.clear()
        return self

    def with_turn_state(self, turn: TurnState) -> ScenarioBuilder:
        """Remplace le tour courant (étape, joueur actif, numéro)."""
        self._require_state().replace_turn_state(turn)
        return self

    def with_priority_player(self, player_index: int) -> ScenarioBuilder:
        """Assigne la priorité au joueur indiqué."""
        self._require_state().turn_engine_set_priority_player(player_index)
        return self

    def with_duel_opening_player(self, player_index: int) -> ScenarioBuilder:
        """Mémorise le premier joueur du duel (pioche initiale)."""
        self._require_state().establish_duel_opening_player(player_index)
        return self

    def add_floating_mana(self, player_index: int, amount: int) -> ScenarioBuilder:
        """Ajoute du mana flottant au joueur."""
        if amount < 0:
            msg = "Le mana ajouté ne peut pas être négatif."
            raise InvalidGameStateError(msg, field_name="amount")
        self._require_state().players[player_index].add_floating_mana(amount)
        return self

    def add_card_in_hand(
        self, player_index: int, catalog_key: str, *, alias: str
    ) -> ScenarioBuilder:
        """Enregistre une carte en main et la lie à un alias stable."""
        if alias in self._aliases:
            msg = "Alias d'objet déjà utilisé dans ce scénario."
            raise InvalidGameStateError(msg, field_name="alias")
        state = self._require_state()
        oid = state.issue_object_id()
        self._aliases[alias] = oid
        state.register_object_at(
            InGameCard(oid, CardReference(catalog_key)),
            ZoneLocation(player_index, ZoneType.HAND),
        )
        return self

    def add_permanent_on_battlefield(
        self,
        player_index: int,
        catalog_key: str,
        *,
        alias: str,
    ) -> ScenarioBuilder:
        """Place un permanent sur le champ et l'enregistre sous ``alias``."""
        if alias in self._aliases:
            msg = "Alias d'objet déjà utilisé dans ce scénario."
            raise InvalidGameStateError(msg, field_name="alias")
        state = self._require_state()
        oid = state.issue_object_id()
        self._aliases[alias] = oid
        state.register_object_at(
            Permanent(oid, CardReference(catalog_key)),
            ZoneLocation(player_index, ZoneType.BATTLEFIELD),
        )
        return self

    def build(self) -> ScenarioContext:
        """Finalise le contexte (``TurnManager`` et :class:`LegalActionService` neufs)."""
        state = self._require_state()
        tm = TurnManager(state, rules=self._rules)
        legal = LegalActionService()
        return ScenarioContext(
            state=state,
            rules=self._rules,
            object_aliases=dict(self._aliases),
            turn_manager=tm,
            legal_service=legal,
        )

    def _require_state(self) -> GameState:
        if self._state is None:
            msg = "Appelez with_two_player_game avant toute autre étape du builder."
            raise InvalidGameStateError(msg, field_name="state")
        return self._state
