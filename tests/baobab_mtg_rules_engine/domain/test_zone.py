"""Tests pour :class:`Zone`."""

import pytest

from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.zone import Zone
from baobab_mtg_rules_engine.domain.zone_type import ZoneType


class TestZone:
    """Ordre et présence dans une zone."""

    def test_append_and_contains(self) -> None:
        """Ajout et test de présence."""
        zone = Zone(ZoneType.HAND, 0)
        oid = GameObjectId(1)
        zone.append(oid)
        assert zone.contains(oid)
        assert zone.object_ids() == (oid,)

    def test_remove(self) -> None:
        """Retrait de la première occurrence."""
        zone = Zone(ZoneType.GRAVEYARD, 0)
        a = GameObjectId(1)
        b = GameObjectId(2)
        zone.append(a)
        zone.append(b)
        zone.remove(a)
        assert zone.object_ids() == (b,)

    def test_remove_missing_raises(self) -> None:
        """Retirer un objet absent lève ``ValueError``."""
        zone = Zone(ZoneType.LIBRARY, 0)
        with pytest.raises(ValueError):
            zone.remove(GameObjectId(99))
