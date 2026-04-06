"""Tests pour :class:`GameStateInspector`."""

from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.observability.game_state_inspector import GameStateInspector


class TestGameStateInspector:
    """Formatage et traces stables."""

    def test_event_trace_tuple_empty(self) -> None:
        """Partie neuve : trace minimale mais stable."""
        state = GameState.new_two_player()
        trace = GameStateInspector.event_trace_tuple(state)
        assert len(trace) >= 1
        names = [t[0] for t in trace]
        assert EventType.GAME_INITIALIZED.name in names

    def test_format_events_non_empty(self) -> None:
        """Le formatage produit au moins une ligne."""
        state = GameState.new_two_player()
        text = GameStateInspector.format_events(state, max_entries=3)
        assert "GAME_INITIALIZED" in text

    def test_snapshot_summary_contains_priority(self) -> None:
        """Le résumé mentionne priorité et étape."""
        state = GameState.new_two_player()
        summary = GameStateInspector.snapshot_summary(state)
        assert "priority=" in summary
        assert "step=" in summary

    def test_format_events_truncates_to_max_entries(self) -> None:
        """max_entries ne garde que les derniers événements."""
        state = GameState.new_two_player()
        for i in range(6):
            state.record_engine_event(EventType.PRIORITY_PASSED, (("idx", i),))
        text = GameStateInspector.format_events(state, max_entries=2)
        assert text.count("PRIORITY_PASSED") == 2
        assert "idx=5" in text or "idx=4" in text
