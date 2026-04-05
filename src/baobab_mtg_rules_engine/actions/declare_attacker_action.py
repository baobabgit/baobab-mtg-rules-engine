"""Action : déclarer une créature attaquante."""

from dataclasses import dataclass
from typing import Any

from baobab_mtg_rules_engine.actions.game_action import GameAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


@dataclass(frozen=True, slots=True)
class DeclareAttackerAction(GameAction):
    """Ajoute une créature à l'ensemble des attaquants (modèle combat simplifié)."""

    creature_object_id: GameObjectId

    @property
    def kind(self) -> SupportedActionKind:
        """:return: :attr:`SupportedActionKind.DECLARE_ATTACKER`."""
        return SupportedActionKind.DECLARE_ATTACKER

    def sort_key(self) -> tuple[Any, ...]:
        """:return: Tri par identifiant de créature."""
        return (self.kind.value, self.creature_object_id.value)
