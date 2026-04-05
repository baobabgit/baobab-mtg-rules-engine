"""Tests pour :class:`SpellOnStack`."""

from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.spell_on_stack import SpellOnStack


class TestSpellOnStack:
    """Sort sur la pile."""

    def test_kind_label(self) -> None:
        """:class:`SpellOnStack` est identifiable dans les événements."""
        spell = SpellOnStack(GameObjectId(1), CardReference("s"))
        assert spell.kind_label == "spell_on_stack"
