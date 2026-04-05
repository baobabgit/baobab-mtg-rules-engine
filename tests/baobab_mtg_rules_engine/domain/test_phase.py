"""Tests pour :class:`Phase`."""

from baobab_mtg_rules_engine.domain.phase import Phase


class TestPhase:
    """Phases de tour."""

    def test_enum_members_exist(self) -> None:
        """Les phases principales du tour sont définies."""
        names = {p.name for p in Phase}
        assert "BEGINNING" in names
        assert "COMBAT" in names
