"""Tests pour :class:`SimpleTarget`."""

import pytest

from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget


class TestSimpleTarget:
    """Constructeurs et tri."""

    def test_for_player(self) -> None:
        """Cible joueur valide pour l'index 0 ou 1."""
        t = SimpleTarget.for_player(1)
        assert t.player_index == 1
        assert t.permanent_object_id is None
        assert t.sort_key()[0] == "player"

    def test_for_permanent(self) -> None:
        """Cible permanent."""
        oid = GameObjectId(4)
        t = SimpleTarget.for_permanent(oid)
        assert t.permanent_object_id == oid
        assert t.player_index is None

    def test_rejects_ambiguous_target(self) -> None:
        """Ni double ni vide : exactement une forme."""
        with pytest.raises(ValueError, match="exclusivement"):
            SimpleTarget(player_index=None, permanent_object_id=None)
        with pytest.raises(ValueError, match="exclusivement"):
            SimpleTarget(player_index=0, permanent_object_id=GameObjectId(1))

    def test_rejects_bad_player_index(self) -> None:
        """Hors 0/1 refusé."""
        with pytest.raises(ValueError, match="duel"):
            SimpleTarget.for_player(2)
