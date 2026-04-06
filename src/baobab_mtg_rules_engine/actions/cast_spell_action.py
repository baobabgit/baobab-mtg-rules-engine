"""Action : lancer un sort simple depuis la main."""

from dataclasses import dataclass, field
from typing import Any

from baobab_mtg_rules_engine.actions.game_action import GameAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget


@dataclass(frozen=True, slots=True)
class CastSpellAction(GameAction):
    """Lance un sort depuis la main en payant le coût indiqué par le port gameplay."""

    spell_object_id: GameObjectId
    targets: tuple[SimpleTarget, ...] = field(default_factory=tuple)

    @property
    def kind(self) -> SupportedActionKind:
        """:return: :attr:`SupportedActionKind.CAST_SPELL`."""
        return SupportedActionKind.CAST_SPELL

    def sort_key(self) -> tuple[Any, ...]:
        """:return: Tri par identifiant d'objet puis cibles (ordre déterministe)."""
        target_keys = tuple(t.sort_key() for t in self.targets)
        return (self.kind.value, self.spell_object_id.value, target_keys)
