"""Action : activer une capacité simple (coût mana générique, sans ciblage complexe)."""

from dataclasses import dataclass
from typing import Any

from baobab_mtg_rules_engine.actions.game_action import GameAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


@dataclass(frozen=True, slots=True)
class ActivateSimpleAbilityAction(GameAction):
    """Active une capacité sur un permanent contrôlé, moyennant un coût entier."""

    permanent_object_id: GameObjectId
    generic_mana_cost: int

    @property
    def kind(self) -> SupportedActionKind:
        """:return: :attr:`SupportedActionKind.ACTIVATE_SIMPLE_ABILITY`."""
        return SupportedActionKind.ACTIVATE_SIMPLE_ABILITY

    def sort_key(self) -> tuple[Any, ...]:
        """:return: Tri par permanent puis coût."""
        return (
            self.kind.value,
            self.permanent_object_id.value,
            self.generic_mana_cost,
        )
