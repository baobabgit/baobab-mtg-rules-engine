"""Action : jouer un terrain depuis la main."""

from dataclasses import dataclass
from typing import Any

from baobab_mtg_rules_engine.actions.game_action import GameAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


@dataclass(frozen=True, slots=True)
class PlayLandAction(GameAction):
    """Joue un terrain identifié en main vers le champ de bataille."""

    land_object_id: GameObjectId

    @property
    def kind(self) -> SupportedActionKind:
        """:return: :attr:`SupportedActionKind.PLAY_LAND`."""
        return SupportedActionKind.PLAY_LAND

    def sort_key(self) -> tuple[Any, ...]:
        """:return: Tri par identifiant d'objet."""
        return (self.kind.value, self.land_object_id.value)
