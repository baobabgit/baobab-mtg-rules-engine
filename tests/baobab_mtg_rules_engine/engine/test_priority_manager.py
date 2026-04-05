"""Tests pour :class:`PriorityManager`."""

from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.spell_on_stack import SpellOnStack
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.engine.priority_manager import PriorityManager


class TestPriorityManager:
    """Passes à pile vide et rotation."""

    def test_active_player_receives_priority_on_assign(self) -> None:
        """Après assignation, le détenteur est le joueur actif."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(1, 1, Step.UPKEEP))
        mgr = PriorityManager(state)
        mgr.assign_to_active_player()
        assert state.priority_player_index == 1
        assert state.consecutive_empty_stack_passes == 0

    def test_two_empty_stack_passes_signal_advance(self) -> None:
        """Deux passes à pile vide demandent l'avancement d'étape."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 1, Step.UPKEEP))
        mgr = PriorityManager(state)
        mgr.assign_to_active_player()
        assert mgr.process_priority_pass() is False
        assert state.priority_player_index == 1
        assert mgr.process_priority_pass() is True

    def test_nonempty_stack_resets_pass_counter_and_rotates(self) -> None:
        """À pile non vide, on alterne la priorité sans compter vers l'avancement."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 1, Step.UPKEEP))
        mgr = PriorityManager(state)
        mgr.assign_to_active_player()
        oid = state.issue_object_id()
        state.register_object_at(
            SpellOnStack(oid, CardReference("x")),
            ZoneLocation(None, ZoneType.STACK),
        )
        state.turn_engine_increment_empty_stack_passes()
        assert mgr.process_priority_pass() is False
        assert state.priority_player_index == 1
        assert state.consecutive_empty_stack_passes == 0
