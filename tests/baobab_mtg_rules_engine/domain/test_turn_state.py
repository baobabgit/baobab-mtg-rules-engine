"""Tests pour :class:`TurnState`."""

import pytest

from baobab_mtg_rules_engine.domain.phase import Phase
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError


class TestTurnState:
    """Cohérence tour / phase / étape."""

    def test_phase_derived_from_step(self) -> None:
        """La phase est dérivée de l'étape courante."""
        turn = TurnState.start_first_turn(0)
        assert turn.step is Step.UNTAP
        assert turn.phase is Phase.BEGINNING

    def test_invalid_turn_number(self) -> None:
        """Un numéro de tour nul ou négatif est refusé."""
        with pytest.raises(InvalidGameStateError, match="turn_number"):
            TurnState(0, 0, Step.UNTAP)

    def test_negative_active_player(self) -> None:
        """Un joueur actif négatif est refusé."""
        with pytest.raises(InvalidGameStateError, match="active_player_index"):
            TurnState(-1, 1, Step.UNTAP)

    def test_start_first_turn_rejects_negative_player(self) -> None:
        """Le joueur initial ne peut pas avoir un index négatif."""
        with pytest.raises(InvalidGameStateError, match="starting_player_index"):
            TurnState.start_first_turn(-1)
