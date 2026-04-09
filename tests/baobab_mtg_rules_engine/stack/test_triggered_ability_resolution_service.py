"""Tests unitaires pour :class:`TriggeredAbilityResolutionService`."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)

from baobab_mtg_rules_engine.domain.ability_on_stack import AbilityOnStack

from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.pending_triggered_ability import PendingTriggeredAbility
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.triggered_ability_definition import TriggeredAbilityDefinition
from baobab_mtg_rules_engine.domain.triggered_ability_stack_object import (
    TriggeredAbilityStackObject,
)
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError
from baobab_mtg_rules_engine.stack.triggered_ability_resolution_service import (
    TriggeredAbilityResolutionService,
)
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget


def _rules() -> InMemoryCardCatalogAdapter:
    return InMemoryCardCatalogAdapter(
        frozenset({"bear"}),
        creature_keys=frozenset({"bear"}),
        creature_power_toughness_by_key={"bear": (2, 2)},
    )


def _stack_trigger(
    state: GameState,
    definition: TriggeredAbilityDefinition,
    *,
    targets: tuple[SimpleTarget, ...] = (),
    controller: int = 0,
) -> GameObjectId:
    pending = PendingTriggeredAbility(
        pending_trigger_id=state.issue_pending_trigger_id(),
        controller_player_index=controller,
        source_object_id=None,
        source_catalog_key="",
        ability_definition=definition,
        trigger_event_sequence=1,
    )
    ability_id = state.issue_object_id()
    state.register_object_at(
        AbilityOnStack(ability_id, source_object_id=None, ability_key=definition.ability_key),
        ZoneLocation(None, ZoneType.STACK),
    )
    state.attach_triggered_ability_view(
        ability_id,
        TriggeredAbilityStackObject(
            ability_object_id=ability_id,
            pending_trigger_id=pending.pending_trigger_id,
            controller_player_index=controller,
            source_object_id=None,
            source_catalog_key="",
            ability_definition=definition,
            targets=targets,
        ),
    )
    return ability_id


class TestTriggeredAbilityResolutionService:
    """Branches de résolution/fizzle des capacités déclenchées."""

    def test_empty_stack_raises(self) -> None:
        """Résoudre sans objet sur la pile est incohérent."""
        with pytest.raises(InvalidGameStateError, match="vide"):
            TriggeredAbilityResolutionService().resolve_top(GameState.new_two_player(), _rules())

    def test_missing_trigger_view_raises(self) -> None:
        """Un sommet sans vue déclenchée associée est refusé."""
        state = GameState.new_two_player()
        oid = state.issue_object_id()
        state.register_object_at(
            AbilityOnStack(oid, source_object_id=None, ability_key="k"),
            ZoneLocation(None, ZoneType.STACK),
        )
        with pytest.raises(InvalidGameStateError, match="Vue"):
            TriggeredAbilityResolutionService().resolve_top(state, _rules())

    def test_damage_player_trigger_resolves(self) -> None:
        """Un trigger ciblant un joueur inflige les dégâts attendus."""
        state = GameState.new_two_player()
        definition = TriggeredAbilityDefinition(
            ability_key="ping",
            trigger_kind="cast_self",
            effect_kind="damage_player",
            target_kind="player",
            amount=2,
        )
        _stack_trigger(state, definition, targets=(SimpleTarget.for_player(1),))
        life_before = state.players[1].life_total
        TriggeredAbilityResolutionService().resolve_top(state, _rules())
        assert state.players[1].life_total == life_before - 2
        assert EventType.TRIGGER_RESOLVED in [e.event_type for e in state.events]

    def test_illegal_creature_target_fizzles(self) -> None:
        """Une cible créature hors champ provoque un fizzle."""
        state = GameState.new_two_player()
        definition = TriggeredAbilityDefinition(
            ability_key="sniper",
            trigger_kind="cast_self",
            effect_kind="destroy_target_creature",
            target_kind="creature",
            amount=1,
        )
        bear = state.issue_object_id()
        state.register_object_at(
            Permanent(bear, CardReference("bear")), ZoneLocation(1, ZoneType.BATTLEFIELD)
        )
        _stack_trigger(state, definition, targets=(SimpleTarget.for_permanent(bear),))
        state.relocate_preserving_identity(bear, ZoneLocation(1, ZoneType.GRAVEYARD))
        TriggeredAbilityResolutionService().resolve_top(state, _rules())
        assert EventType.TRIGGER_FIZZLED in [e.event_type for e in state.events]

    def test_damage_player_without_player_target_fizzles(self) -> None:
        """Une cible incohérente pour damage_player provoque un fizzle."""
        state = GameState.new_two_player()
        definition = TriggeredAbilityDefinition(
            ability_key="ping",
            trigger_kind="cast_self",
            effect_kind="damage_player",
            target_kind="player",
            amount=1,
        )
        _stack_trigger(state, definition, targets=(SimpleTarget.for_permanent(GameObjectId(99)),))
        TriggeredAbilityResolutionService().resolve_top(state, _rules())
        assert EventType.TRIGGER_FIZZLED in [e.event_type for e in state.events]

    def test_destroy_without_creature_target_fizzles(self) -> None:
        """Une cible incohérente pour destroy_target_creature provoque un fizzle."""
        state = GameState.new_two_player()
        definition = TriggeredAbilityDefinition(
            ability_key="sniper",
            trigger_kind="cast_self",
            effect_kind="destroy_target_creature",
            target_kind="creature",
            amount=1,
        )
        _stack_trigger(state, definition, targets=(SimpleTarget.for_player(1),))
        TriggeredAbilityResolutionService().resolve_top(state, _rules())
        assert EventType.TRIGGER_FIZZLED in [e.event_type for e in state.events]

    def test_damage_player_target_missing_player_index_raises(self) -> None:
        """Si la validation est contournée, l'absence de player_index lève une erreur."""
        state = GameState.new_two_player()
        definition = TriggeredAbilityDefinition(
            ability_key="ping",
            trigger_kind="cast_self",
            effect_kind="damage_player",
            target_kind="player",
            amount=1,
        )
        ability_id = _stack_trigger(state, definition, targets=(SimpleTarget.for_player(1),))
        view = state.get_triggered_ability_view(ability_id)
        assert view is not None
        state.detach_triggered_ability_view(ability_id)
        state.attach_triggered_ability_view(
            ability_id,
            TriggeredAbilityStackObject(
                ability_object_id=view.ability_object_id,
                pending_trigger_id=view.pending_trigger_id,
                controller_player_index=view.controller_player_index,
                source_object_id=view.source_object_id,
                source_catalog_key=view.source_catalog_key,
                ability_definition=view.ability_definition,
                targets=(
                    # Objet volontairement invalide (pas un SimpleTarget valide) pour couvrir
                    # la garde interne de _resolve_damage_player.
                    SimpleTarget.for_permanent(GameObjectId(1)),
                ),
            ),
        )
        with patch.object(
            TriggeredAbilityResolutionService,
            "_targets_legal_at_resolution",
            return_value=True,
        ):
            with pytest.raises(InvalidGameStateError, match="cible joueur"):
                TriggeredAbilityResolutionService().resolve_top(state, _rules())

    def test_destroy_target_missing_creature_id_raises(self) -> None:
        """Si la validation est contournée, l'absence de permanent_object_id lève une erreur."""
        state = GameState.new_two_player()
        definition = TriggeredAbilityDefinition(
            ability_key="sniper",
            trigger_kind="cast_self",
            effect_kind="destroy_target_creature",
            target_kind="creature",
            amount=1,
        )
        ability_id = _stack_trigger(
            state, definition, targets=(SimpleTarget.for_permanent(GameObjectId(1)),)
        )
        view = state.get_triggered_ability_view(ability_id)
        assert view is not None
        state.detach_triggered_ability_view(ability_id)
        state.attach_triggered_ability_view(
            ability_id,
            TriggeredAbilityStackObject(
                ability_object_id=view.ability_object_id,
                pending_trigger_id=view.pending_trigger_id,
                controller_player_index=view.controller_player_index,
                source_object_id=view.source_object_id,
                source_catalog_key=view.source_catalog_key,
                ability_definition=view.ability_definition,
                targets=(
                    # Objet volontairement invalide (pas un SimpleTarget valide) pour couvrir
                    # la garde interne de _resolve_destroy_target_creature.
                    SimpleTarget.for_player(1),
                ),
            ),
        )
        with patch.object(
            TriggeredAbilityResolutionService,
            "_targets_legal_at_resolution",
            return_value=True,
        ):
            with pytest.raises(InvalidGameStateError, match="cible créature"):
                TriggeredAbilityResolutionService().resolve_top(state, _rules())

    def test_destroy_target_creature_moves_to_graveyard(self) -> None:
        """La destruction ciblée déplace la créature vers le cimetière."""
        state = GameState.new_two_player()
        definition = TriggeredAbilityDefinition(
            ability_key="sniper",
            trigger_kind="cast_self",
            effect_kind="destroy_target_creature",
            target_kind="creature",
            amount=1,
        )
        bear = state.issue_object_id()
        state.register_object_at(
            Permanent(bear, CardReference("bear")), ZoneLocation(1, ZoneType.BATTLEFIELD)
        )
        _stack_trigger(state, definition, targets=(SimpleTarget.for_permanent(bear),))
        TriggeredAbilityResolutionService().resolve_top(state, _rules())
        loc = state.find_location(bear)
        assert loc.zone_type is ZoneType.GRAVEYARD
        assert EventType.CREATURE_DESTROYED in [e.event_type for e in state.events]

    def test_draw_cards_trigger_draws_and_logs(self) -> None:
        """Un trigger de pioche déplace des cartes de bibliothèque vers main."""
        state = GameState.new_two_player()
        for i in range(2):
            oid = state.issue_object_id()
            state.register_object_at(
                InGameCard(oid, CardReference(f"c{i}")),
                ZoneLocation(0, ZoneType.LIBRARY),
            )
        definition = TriggeredAbilityDefinition(
            ability_key="draw",
            trigger_kind="cast_self",
            effect_kind="draw_cards",
            amount=2,
        )
        _stack_trigger(state, definition)
        TriggeredAbilityResolutionService().resolve_top(state, _rules())
        assert len(state.players[0].zone(ZoneType.HAND).object_ids()) == 2
        assert EventType.TURN_DRAW_PERFORMED in [e.event_type for e in state.events]
