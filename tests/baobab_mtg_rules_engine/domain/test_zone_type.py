"""Tests pour :class:`ZoneType`."""

from baobab_mtg_rules_engine.domain.zone_type import ZoneType


class TestZoneType:
    """Énumération des zones."""

    def test_expected_zone_variants_exist(self) -> None:
        """Les zones usuelles du modèle sont définies (pile, main, champ, etc.)."""
        names = {z.name for z in ZoneType}
        assert "STACK" in names
        assert "HAND" in names
        assert "BATTLEFIELD" in names
