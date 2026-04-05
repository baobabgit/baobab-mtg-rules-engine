"""Tests pour :class:`GameObjectId`."""

import pytest

from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


class TestGameObjectId:
    """Égalité et validation des identifiants d'objet."""

    def test_equality_and_hash(self) -> None:
        """Deux identifiants de même valeur sont égaux et hashables de façon cohérente."""
        a = GameObjectId(1)
        b = GameObjectId(1)
        assert a == b
        assert hash(a) == hash(b)

    def test_inequality(self) -> None:
        """Des valeurs distinctes produisent des identifiants distincts."""
        assert GameObjectId(1) != GameObjectId(2)

    def test_rejects_non_positive(self) -> None:
        """Les valeurs non strictement positives sont refusées."""
        with pytest.raises(ValueError, match="strictement positif"):
            GameObjectId(0)
