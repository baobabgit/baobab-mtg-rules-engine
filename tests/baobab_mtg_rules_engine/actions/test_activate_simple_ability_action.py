"""Tests pour :class:`ActivateSimpleAbilityAction`."""

from baobab_mtg_rules_engine.actions.activate_simple_ability_action import (
    ActivateSimpleAbilityAction,
)
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


class TestActivateSimpleAbilityAction:
    """Tri par permanent puis coût."""

    def test_kind_and_sort_key(self) -> None:
        """Le coût générique participe au tri déterministe."""
        act = ActivateSimpleAbilityAction(GameObjectId(7), 2)
        assert act.kind is SupportedActionKind.ACTIVATE_SIMPLE_ABILITY
        assert act.sort_key() == (SupportedActionKind.ACTIVATE_SIMPLE_ABILITY.value, 7, 2)
