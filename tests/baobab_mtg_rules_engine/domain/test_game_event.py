"""Tests pour :class:`GameEvent`."""

from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_event import GameEvent


class TestGameEvent:
    """Immutabilité et charge utile."""

    def test_frozen_payload(self) -> None:
        """Les événements sont immuables et portent une charge typée."""
        payload = (("k", 1), ("z", "a"))
        event = GameEvent(sequence=1, event_type=EventType.OBJECT_REGISTERED, payload=payload)
        assert event.sequence == 1
        assert event.event_type is EventType.OBJECT_REGISTERED
        assert event.payload == payload
