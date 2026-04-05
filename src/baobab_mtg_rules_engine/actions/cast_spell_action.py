"""Action : lancer un sort simple depuis la main."""

from dataclasses import dataclass
from typing import Any

from baobab_mtg_rules_engine.actions.game_action import GameAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


@dataclass(frozen=True, slots=True)
class CastSpellAction(GameAction):
    """Lance un sort depuis la main en payant le coût indiqué par le port gameplay."""

    spell_object_id: GameObjectId

    @property
    def kind(self) -> SupportedActionKind:
        """:return: :attr:`SupportedActionKind.CAST_SPELL`."""
        return SupportedActionKind.CAST_SPELL

    def sort_key(self) -> tuple[Any, ...]:
        """:return: Tri par identifiant d'objet."""
        return (self.kind.value, self.spell_object_id.value)
