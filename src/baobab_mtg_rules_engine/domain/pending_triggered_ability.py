"""Représentation d'une capacité déclenchée détectée mais pas encore empilée."""

from dataclasses import dataclass

from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.triggered_ability_definition import TriggeredAbilityDefinition


@dataclass(frozen=True, slots=True)
class PendingTriggeredAbility:
    """Entrée de file d'attente de trigger avant mise sur la pile."""

    pending_trigger_id: int
    controller_player_index: int
    source_object_id: GameObjectId | None
    source_catalog_key: str
    ability_definition: TriggeredAbilityDefinition
    trigger_event_sequence: int
