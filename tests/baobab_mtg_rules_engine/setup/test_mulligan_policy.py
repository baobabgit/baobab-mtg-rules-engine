"""Tests pour :class:`MulliganPolicy`."""

import pytest

from baobab_mtg_rules_engine.setup.mulligan_policy import MulliganPolicy


class TestMulliganPolicy:
    """Tailles de main documentées."""

    def test_opening_seven(self) -> None:
        """Avant mulligan la main attendue fait sept cartes."""
        policy = MulliganPolicy()
        assert policy.hand_size_after_mulligans(0) == 7

    def test_after_one_mulligan_six(self) -> None:
        """Un mulligan parisien réduit la prochaine main à six cartes."""
        policy = MulliganPolicy()
        assert policy.hand_size_after_mulligans(1) == 6

    def test_rejects_negative_depth(self) -> None:
        """Les profondeurs négatives sont refusées."""
        with pytest.raises(ValueError, match="négatif"):
            MulliganPolicy().hand_size_after_mulligans(-1)
