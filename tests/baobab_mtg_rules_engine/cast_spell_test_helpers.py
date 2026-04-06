"""Helpers partagés pour tests de lancement et résolution de sorts."""

from __future__ import annotations

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.casting.spell_cast_service import SpellCastService
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget


def kill_spell_rules_targeting_creature() -> InMemoryCardCatalogAdapter:
    """Catalogue minimal : sort ``kill`` ciblant une créature ``bear``."""
    return InMemoryCardCatalogAdapter(
        frozenset({"kill", "bear"}),
        sorcery_spell_keys=frozenset({"kill"}),
        creature_keys=frozenset({"bear"}),
        spell_mana_cost_by_key={"kill": 1},
        spell_target_kind_by_key={"kill": "creature"},
    )


def cast_spell_from_hand(
    state: GameState,
    rules: CardGameplayPort,
    *,
    caster_player_index: int,
    spell_hand_object_id: GameObjectId,
    targets: tuple[SimpleTarget, ...] = (),
) -> GameObjectId:
    """Lance un sort via :class:`SpellCastService` (réduction de duplication en tests)."""
    return SpellCastService().cast_spell(
        state,
        rules,
        caster_player_index=caster_player_index,
        spell_hand_object_id=spell_hand_object_id,
        targets=targets,
    )
