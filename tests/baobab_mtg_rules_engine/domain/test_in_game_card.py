"""Tests pour :class:`InGameCard`."""

from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard


class TestInGameCard:
    """Lien entre identifiant partie et référence catalogue."""

    def test_holds_card_reference(self) -> None:
        """La référence catalogue est distincte de l'identifiant d'objet."""
        ref = CardReference("oracle:42")
        oid = GameObjectId(3)
        card = InGameCard(oid, ref)
        assert card.card_reference == ref
        assert card.object_id == oid
        assert card.kind_label == "in_game_card"
