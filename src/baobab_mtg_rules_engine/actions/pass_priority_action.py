"""Action : passer la priorité."""

from dataclasses import dataclass
from typing import Any

from baobab_mtg_rules_engine.actions.game_action import GameAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind


@dataclass(frozen=True, slots=True)
class PassPriorityAction(GameAction):
    """Passe la priorité au joueur suivant selon les règles du tour."""

    @property
    def kind(self) -> SupportedActionKind:
        """:return: :attr:`SupportedActionKind.PASS_PRIORITY`."""
        return SupportedActionKind.PASS_PRIORITY

    def sort_key(self) -> tuple[Any, ...]:
        """:return: Tri minimal avant toutes les autres actions."""
        return (self.kind.value,)
