"""Tests pour :class:`CardReference`."""

import pytest

from baobab_mtg_rules_engine.domain.card_reference import CardReference


class TestCardReference:
    """Value object de référence catalogue."""

    def test_equality(self) -> None:
        """Même clé catalogue implique égalité."""
        ref_a = CardReference("oracle:123")
        ref_b = CardReference("oracle:123")
        assert ref_a == ref_b

    def test_distinct_keys(self) -> None:
        """Des clés différentes ne sont pas égales."""
        assert CardReference("a") != CardReference("b")

    def test_rejects_empty_key(self) -> None:
        """Une clé vide est refusée."""
        with pytest.raises(ValueError, match="vide"):
            CardReference("")
