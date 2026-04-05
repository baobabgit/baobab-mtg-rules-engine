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

    def test_replace_ordered_contents_same_multiset(self) -> None:
        """Une permutation valide remplace l'ordre sans changer le contenu."""
        zone = Zone(ZoneType.LIBRARY, 0)
        a = GameObjectId(1)
        b = GameObjectId(2)
        c = GameObjectId(3)
        zone.append(a)
        zone.append(b)
        zone.append(c)
        zone.replace_ordered_contents((c, a, b))
        assert zone.object_ids() == (c, a, b)

    def test_replace_ordered_contents_wrong_multiset_raises(self) -> None:
        """Un multi-ensemble différent est refusé."""
        zone = Zone(ZoneType.LIBRARY, 0)
        zone.append(GameObjectId(1))
        zone.append(GameObjectId(2))
        with pytest.raises(ValueError, match="même ensemble"):
            zone.replace_ordered_contents((GameObjectId(1), GameObjectId(1)))

    def test_replace_ordered_contents_duplicate_count_mismatch_raises(self) -> None:
        """Les doublons doivent correspondre exactement (comptage)."""
        zone = Zone(ZoneType.LIBRARY, 0)
        x = GameObjectId(10)
        zone.append(x)
        zone.append(x)
        with pytest.raises(ValueError, match="même ensemble"):
            zone.replace_ordered_contents((x,))
