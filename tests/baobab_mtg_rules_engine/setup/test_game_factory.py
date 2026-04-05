"""Tests pour :class:`GameFactory`."""

from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.setup.callback_mulligan_choice import CallbackMulliganChoice
from baobab_mtg_rules_engine.setup.game_factory import GameFactory
from baobab_mtg_rules_engine.setup.game_setup_request import GameSetupRequest

from .deck_test_utils import (
    make_catalog_two_prefixes,
    make_game_factory_with_two_standard_decks,
    make_sixty_card_deck,
)


class TestGameFactory:
    """Setup nominal et cohérence des zones."""

    def test_nominal_setup_playable_hands(self) -> None:
        """Deux decks valides produisent une partie avec mains de sept cartes."""
        catalog = make_catalog_two_prefixes()
        factory = GameFactory(catalog)
        deck0 = make_sixty_card_deck(name="A", prefix="c")
        deck1 = make_sixty_card_deck(name="B", prefix="d")
        request = GameSetupRequest(
            game_id="g1",
            player_names=("P0", "P1"),
            decks=(deck0, deck1),
            rng_seed=42,
            starting_player=0,
        )
        always_keep = CallbackMulliganChoice(lambda _p, _d, _h: False)
        game = factory.create_game(request, always_keep)
        assert game.game_id == "g1"
        for idx in (0, 1):
            hand = game.state.players[idx].zone(ZoneType.HAND).object_ids()
            library = game.state.players[idx].zone(ZoneType.LIBRARY).object_ids()
            assert len(hand) == 7
            assert len(library) == 53
        assert game.state.turn_state.active_player_index == 0
        types = [e.event_type for e in game.state.events]
        assert EventType.SETUP_FIRST_TURN_READY in types

    def test_same_seed_same_library_order(self) -> None:
        """Avec la même graine, l'ordre des bibliothèques est identique."""
        factory, decks = make_game_factory_with_two_standard_decks()
        req = GameSetupRequest(
            game_id="x",
            player_names=("a", "b"),
            decks=decks,
            rng_seed=999,
            starting_player=0,
        )
        keep = CallbackMulliganChoice(lambda _p, _d, _h: False)
        g1 = factory.create_game(req, keep)
        g2 = factory.create_game(req, keep)
        for idx in (0, 1):
            z1 = g1.state.players[idx].zone(ZoneType.LIBRARY).object_ids()
            z2 = g2.state.players[idx].zone(ZoneType.LIBRARY).object_ids()
            assert z1 == z2

    def test_starting_player_from_rng_when_none(self) -> None:
        """Si ``starting_player`` vaut ``None``, le tirage dépend de la graine."""
        factory, decks = make_game_factory_with_two_standard_decks()
        req = GameSetupRequest(
            game_id="y",
            player_names=("a", "b"),
            decks=decks,
            rng_seed=12345,
            starting_player=None,
        )
        keep = CallbackMulliganChoice(lambda _p, _d, _h: False)
        game = factory.create_game(req, keep)
        assert game.state.turn_state.active_player_index in (0, 1)
