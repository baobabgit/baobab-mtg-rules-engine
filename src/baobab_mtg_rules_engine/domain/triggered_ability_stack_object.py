"""Vue métier d'une capacité déclenchée présente sur la pile."""

from dataclasses import dataclass

from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.triggered_ability_definition import TriggeredAbilityDefinition
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget


@dataclass(frozen=True, slots=True)
class TriggeredAbilityStackObject:
    """Métadonnées nécessaires à la résolution d'une capacité déclenchée sur la pile."""

    ability_object_id: GameObjectId
    pending_trigger_id: int
    controller_player_index: int
    source_object_id: GameObjectId | None
    source_catalog_key: str
    ability_definition: TriggeredAbilityDefinition
    targets: tuple[SimpleTarget, ...]
