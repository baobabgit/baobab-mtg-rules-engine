"""Tests pour :class:`Permanent`."""

from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.permanent import Permanent


class TestPermanent:
    """Kind label et héritage carte en jeu."""

    def test_kind_label(self) -> None:
        """:class:`Permanent` expose un libellé stable."""
        perm = Permanent(GameObjectId(1), CardReference("c"))
        assert perm.kind_label == "permanent"
