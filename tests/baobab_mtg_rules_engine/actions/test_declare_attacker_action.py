"""Tests pour :class:`DeclareAttackerAction`."""

from baobab_mtg_rules_engine.actions.declare_attacker_action import DeclareAttackerAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


class TestDeclareAttackerAction:
    """Tri par créature attaquante."""

    def test_kind_and_sort_key(self) -> None:
        """L'identifiant de la créature ordonne les attaquants."""
        dec = DeclareAttackerAction(GameObjectId(11))
        assert dec.kind is SupportedActionKind.DECLARE_ATTACKER
        assert dec.sort_key() == (SupportedActionKind.DECLARE_ATTACKER.value, 11)
