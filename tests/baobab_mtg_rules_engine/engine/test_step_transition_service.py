"""Tests pour :class:`StepTransitionService`."""

from enum import Enum, auto

import pytest

from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.engine.step_transition_service import StepTransitionService
from baobab_mtg_rules_engine.exceptions.unsupported_rule_exception import UnsupportedRuleException


class TestStepTransitionService:
    """Séquence d'étapes et passage au joueur suivant."""

    def test_successor_chain_within_turn(self) -> None:
        """L'ordre UNTAP → … → CLEANUP est déterministe."""
        svc = StepTransitionService()
        assert svc.successor_step(Step.UNTAP) is Step.UPKEEP
        assert svc.successor_step(Step.UPKEEP) is Step.DRAW
        assert svc.successor_step(Step.DRAW) is Step.MAIN_PRECOMBAT
        assert svc.successor_step(Step.END_TURN) is Step.CLEANUP
        assert svc.successor_step(Step.CLEANUP) is None

    def test_turn_state_after_cleanup_advances_player_and_turn(self) -> None:
        """Après nettoyage, l'adversaire prend le tour suivant en UNTAP."""
        svc = StepTransitionService()
        ts = TurnState(active_player_index=0, turn_number=3, step=Step.CLEANUP)
        nxt = svc.turn_state_after_cleanup(ts)
        assert nxt.active_player_index == 1
        assert nxt.turn_number == 4
        assert nxt.step is Step.UNTAP

    def test_unknown_step_in_sequence_raises(self) -> None:
        """Une étape absente de la séquence interne est refusée explicitement."""

        class _ForeignStep(Enum):
            OTHER = auto()

        svc = StepTransitionService()
        with pytest.raises(UnsupportedRuleException, match="boucle"):
            svc.successor_step(_ForeignStep.OTHER)  # type: ignore[arg-type]
