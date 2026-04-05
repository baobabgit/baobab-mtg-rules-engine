"""Action : déclarer un bloqueur simple sur un attaquant."""

from dataclasses import dataclass
from typing import Any

from baobab_mtg_rules_engine.actions.game_action import GameAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


@dataclass(frozen=True, slots=True)
class DeclareBlockerAction(GameAction):
    """Associe une créature défensive à un attaquant déjà déclaré."""

    blocker_object_id: GameObjectId
    attacker_object_id: GameObjectId

    @property
    def kind(self) -> SupportedActionKind:
        """:return: :attr:`SupportedActionKind.DECLARE_BLOCKER`."""
        return SupportedActionKind.DECLARE_BLOCKER

    def sort_key(self) -> tuple[Any, ...]:
        """:return: Tri par bloqueur puis attaquant."""
        return (
            self.kind.value,
            self.blocker_object_id.value,
            self.attacker_object_id.value,
        )
