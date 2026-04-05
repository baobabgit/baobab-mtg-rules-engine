"""Tests pour :class:`ZoneLocation`."""

import pytest

from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError


class TestZoneLocation:
    """Invariants d'emplacement zone / pile."""

    def test_stack_has_no_owner(self) -> None:
        """La pile accepte ``player_index=None``."""
        loc = ZoneLocation(None, ZoneType.STACK)
        assert loc.player_index is None
        assert loc.zone_type is ZoneType.STACK

    def test_stack_rejects_owner(self) -> None:
        """La pile ne doit pas avoir de joueur propriétaire."""
        with pytest.raises(InvalidGameStateError, match="pile"):
            ZoneLocation(0, ZoneType.STACK)

    def test_player_zone_requires_owner(self) -> None:
        """Une zone joueur exige un index joueur."""
        with pytest.raises(InvalidGameStateError, match="pile"):
            ZoneLocation(None, ZoneType.HAND)

    def test_negative_player_rejected(self) -> None:
        """Un index joueur négatif est invalide."""
        with pytest.raises(InvalidGameStateError, match="négatif"):
            ZoneLocation(-1, ZoneType.HAND)
