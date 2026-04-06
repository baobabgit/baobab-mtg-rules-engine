"""Tests pour :class:`EventType`."""

from baobab_mtg_rules_engine.domain.event_type import EventType


class TestEventType:
    """Types d'événements du journal."""

    def test_core_event_types_exist(self) -> None:
        """Les catégories minimales du journal sont présentes."""
        names = {e.name for e in EventType}
        assert "GAME_INITIALIZED" in names
        assert "OBJECT_RELOCATED" in names
        assert "SPELL_RESOLVED" in names
        assert "SPELL_FIZZLED" in names
        assert "PLAYER_DAMAGED" in names
