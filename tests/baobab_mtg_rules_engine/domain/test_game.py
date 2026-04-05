"""Tests pour :class:`Game`."""

from baobab_mtg_rules_engine.domain.game import Game
from baobab_mtg_rules_engine.domain.game_state import GameState


class TestGame:
    """Fabrique de partie et lien avec l'état."""

    def test_create_two_player_wraps_state(self) -> None:
        """La fabrique attache un :class:`GameState` valide."""
        session = Game.create_two_player("match-001", names=("P1", "P2"))
        assert session.game_id == "match-001"
        assert isinstance(session.state, GameState)
        assert session.state.players[1].name == "P2"
