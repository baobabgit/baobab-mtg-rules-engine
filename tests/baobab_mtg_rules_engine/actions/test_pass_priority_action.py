"""Tests pour :class:`PassPriorityAction`."""

from baobab_mtg_rules_engine.actions.pass_priority_action import PassPriorityAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind


class TestPassPriorityAction:
    """Tri et égalité des passes."""

    def test_kind_and_sort_key(self) -> None:
        """La passe est triée en premier parmi les actions."""
        a = PassPriorityAction()
        assert a.kind is SupportedActionKind.PASS_PRIORITY
        assert a.sort_key()[0] == SupportedActionKind.PASS_PRIORITY.value

    def test_empty_instances_compare_equal(self) -> None:
        """Deux passes vides sont interchangeables pour l'ensemble légal."""
        assert PassPriorityAction() == PassPriorityAction()
