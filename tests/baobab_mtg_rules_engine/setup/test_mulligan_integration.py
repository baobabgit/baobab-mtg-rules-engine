"""Tests d'intégration du mulligan dans le setup."""

from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.setup.callback_mulligan_choice import CallbackMulliganChoice
from baobab_mtg_rules_engine.setup.game_setup_request import GameSetupRequest

from .deck_test_utils import make_game_factory_with_two_standard_decks


class TestMulliganIntegration:
    """Mulligan parisien avec décisions scriptées."""

    def test_one_mulligan_reduces_hand_to_six(self) -> None:
        """Un mulligan du joueur 0 mène à une main de six cartes."""
        factory, decks = make_game_factory_with_two_standard_decks()
        request = GameSetupRequest(
            game_id="m1",
            player_names=("P0", "P1"),
            decks=decks,
            rng_seed=7,
            starting_player=0,
        )

        def choice(player: int, depth: int, _hand: object) -> bool:
            return player == 0 and depth == 0

        game = factory.create_game(request, CallbackMulliganChoice(choice))
        p0_hand = game.state.players[0].zone(ZoneType.HAND).object_ids()
        p1_hand = game.state.players[1].zone(ZoneType.HAND).object_ids()
        assert len(p0_hand) == 6
        assert len(p1_hand) == 7
