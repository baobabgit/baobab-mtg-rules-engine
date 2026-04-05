"""Tests pour :class:`DeclareBlockerAction`."""

from baobab_mtg_rules_engine.actions.declare_blocker_action import DeclareBlockerAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


class TestDeclareBlockerAction:
    """Tri par bloqueur puis attaquant."""

    def test_kind_and_sort_key(self) -> None:
        """Les paires (bloqueur, attaquant) sont ordonnées lexicographiquement."""
        dec = DeclareBlockerAction(GameObjectId(4), GameObjectId(9))
        assert dec.kind is SupportedActionKind.DECLARE_BLOCKER
        assert dec.sort_key() == (SupportedActionKind.DECLARE_BLOCKER.value, 4, 9)
