"""Tests d'intégration du noyau des capacités déclenchées (feature 09)."""

from __future__ import annotations

import pytest

from baobab_mtg_rules_engine.actions.cast_spell_action import CastSpellAction
from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.triggered_ability_definition import TriggeredAbilityDefinition
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.engine.legal_action_service import LegalActionService
from baobab_mtg_rules_engine.engine.turn_manager import TurnManager
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError


def _trigger_rules() -> InMemoryCardCatalogAdapter:
    cast_trigger = TriggeredAbilityDefinition(
        ability_key="chant_on_cast",
        trigger_kind="cast_self",
        effect_kind="damage_opponent",
        amount=1,
    )
    etb_trigger = TriggeredAbilityDefinition(
        ability_key="watcher_etb",
        trigger_kind="etb_self",
        effect_kind="damage_opponent",
        amount=1,
    )
    dies_trigger = TriggeredAbilityDefinition(
        ability_key="deathpriest_dies",
        trigger_kind="dies_self",
        effect_kind="damage_opponent",
        amount=2,
    )
    upkeep_damage = TriggeredAbilityDefinition(
        ability_key="upkeep_ping",
        trigger_kind="begin_step",
        trigger_step="UPKEEP",
        trigger_step_scope="any",
        effect_kind="damage_opponent",
        amount=1,
    )
    upkeep_destroy_creature = TriggeredAbilityDefinition(
        ability_key="upkeep_destroy",
        trigger_kind="begin_step",
        trigger_step="UPKEEP",
        trigger_step_scope="you",
        effect_kind="destroy_target_creature",
        target_kind="creature",
        amount=1,
    )
    return InMemoryCardCatalogAdapter(
        frozenset(
            {
                "chant",
                "watcher",
                "deathpriest",
                "upkeep_mage",
                "sniper",
                "bear",
            }
        ),
        creature_keys=frozenset({"watcher", "deathpriest", "upkeep_mage", "sniper", "bear"}),
        sorcery_spell_keys=frozenset({"chant"}),
        creature_spell_keys=frozenset({"watcher"}),
        spell_mana_cost_by_key={"chant": 1, "watcher": 1},
        triggered_abilities_by_key={
            "chant": (cast_trigger,),
            "watcher": (etb_trigger,),
            "deathpriest": (dies_trigger,),
            "upkeep_mage": (upkeep_damage,),
            "sniper": (upkeep_destroy_creature,),
        },
        creature_power_toughness_by_key={
            "watcher": (2, 2),
            "deathpriest": (1, 1),
            "upkeep_mage": (1, 2),
            "sniper": (1, 1),
            "bear": (2, 2),
        },
    )


def _register_hand_card(state: GameState, player: int, key: str) -> GameObjectId:
    oid = state.issue_object_id()
    state.register_object_at(
        InGameCard(oid, CardReference(key)), ZoneLocation(player, ZoneType.HAND)
    )
    return oid


def _register_permanent(state: GameState, player: int, key: str) -> GameObjectId:
    oid = state.issue_object_id()
    state.register_object_at(
        Permanent(oid, CardReference(key)),
        ZoneLocation(player, ZoneType.BATTLEFIELD),
    )
    return oid


def _event_count(state: GameState, kind: EventType) -> int:
    return sum(1 for e in state.events if e.event_type is kind)


def _first_event_index(state: GameState, kind: EventType) -> int:
    for idx, event in enumerate(state.events):
        if event.event_type is kind:
            return idx
    raise AssertionError(f"Événement introuvable: {kind.name}")


class TestTriggeredAbilityFlow:
    """Détection, file d'attente, empilement, APNAP et résolution/fizzle."""

    def test_cast_trigger_is_queued_and_stacked_before_first_pass(self) -> None:
        """Un trigger sur cast est empilé avant traitement de la passe."""
        rules = _trigger_rules()
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        chant = _register_hand_card(state, 0, "chant")
        state.players[0].add_floating_mana(1)
        tm = TurnManager(state, rules=rules)
        LegalActionService().apply_action(
            state,
            rules,
            0,
            CastSpellAction(chant, ()),
            tm,
        )
        passed_before = _event_count(state, EventType.PRIORITY_PASSED)
        tm.pass_priority()
        assert _event_count(state, EventType.PRIORITY_PASSED) == passed_before
        stack_ids = state.stack_zone.object_ids()
        assert len(stack_ids) == 2
        top_view = state.get_triggered_ability_view(stack_ids[-1])
        assert top_view is not None
        assert top_view.ability_definition.ability_key == "chant_on_cast"
        tm.pass_priority()
        tm.pass_priority()
        assert state.players[1].life_total == 19
        assert EventType.TRIGGER_RESOLVED in [e.event_type for e in state.events]

    def test_etb_trigger_detected_after_spell_resolution(self) -> None:
        """Le trigger ETB apparaît après la résolution du sort, puis se résout normalement."""
        rules = _trigger_rules()
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        watcher = _register_hand_card(state, 0, "watcher")
        state.players[0].add_floating_mana(1)
        tm = TurnManager(state, rules=rules)
        LegalActionService().apply_action(
            state,
            rules,
            0,
            CastSpellAction(watcher, ()),
            tm,
        )
        tm.pass_priority()
        tm.pass_priority()
        assert _first_event_index(state, EventType.SPELL_RESOLVED) < _first_event_index(
            state, EventType.TRIGGER_DETECTED
        )
        stack_ids = state.stack_zone.object_ids()
        assert len(stack_ids) == 1
        top_view = state.get_triggered_ability_view(stack_ids[-1])
        assert top_view is not None
        assert top_view.ability_definition.ability_key == "watcher_etb"
        tm.pass_priority()
        tm.pass_priority()
        assert state.players[1].life_total == 19
        assert EventType.TRIGGER_RESOLVED in [e.event_type for e in state.events]

    def test_dies_trigger_queued_then_stacked(self) -> None:
        """Un trigger de mort n'est pas perdu et passe bien par la file puis la pile."""
        rules = _trigger_rules()
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        priest = _register_permanent(state, 0, "deathpriest")
        tm = TurnManager(state, rules=rules)
        state.relocate_preserving_identity(priest, ZoneLocation(0, ZoneType.GRAVEYARD))
        passed_before = _event_count(state, EventType.PRIORITY_PASSED)
        tm.pass_priority()
        assert _event_count(state, EventType.PRIORITY_PASSED) == passed_before
        assert len(state.stack_zone.object_ids()) == 1
        assert EventType.TRIGGER_QUEUED in [e.event_type for e in state.events]
        tm.pass_priority()
        tm.pass_priority()
        assert state.players[1].life_total == 18

    def test_upkeep_triggers_follow_apnap_deterministic_order(self) -> None:
        """En duel, les triggers d'entretien AP puis NAP sont empilés de façon déterministe."""
        rules = _trigger_rules()
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.UPKEEP))
        state.turn_engine_set_priority_player(0)
        _register_permanent(state, 0, "upkeep_mage")
        _register_permanent(state, 1, "upkeep_mage")
        tm = TurnManager(state, rules=rules)
        tm.open_current_step()
        stack_ids = state.stack_zone.object_ids()
        assert len(stack_ids) == 2
        first = state.get_triggered_ability_view(stack_ids[0])
        second = state.get_triggered_ability_view(stack_ids[1])
        assert first is not None and second is not None
        assert first.controller_player_index == 0
        assert second.controller_player_index == 1
        tm.pass_priority()
        tm.pass_priority()
        assert state.players[0].life_total == 19
        assert state.players[1].life_total == 20
        tm.pass_priority()
        tm.pass_priority()
        assert state.players[0].life_total == 19
        assert state.players[1].life_total == 19

    def test_trigger_fizzles_when_target_creature_becomes_illegal(self) -> None:
        """Une capacité déclenchée ciblée fizzled si la cible quitte le champ avant résolution."""
        rules = _trigger_rules()
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.UPKEEP))
        state.turn_engine_set_priority_player(0)
        bear = _register_permanent(state, 1, "bear")
        _register_permanent(state, 0, "sniper")
        tm = TurnManager(state, rules=rules)
        tm.open_current_step()
        stack_ids = state.stack_zone.object_ids()
        assert len(stack_ids) == 1
        view = state.get_triggered_ability_view(stack_ids[-1])
        assert view is not None
        assert len(view.targets) == 1
        assert view.targets[0].permanent_object_id == bear
        state.relocate_preserving_identity(bear, ZoneLocation(1, ZoneType.GRAVEYARD))
        tm.pass_priority()
        tm.pass_priority()
        assert EventType.TRIGGER_FIZZLED in [e.event_type for e in state.events]


class TestTriggeredAbilityFlowDefensiveBranches:
    """Couvre des branches de garde pour le détecteur/résolveur."""

    def test_invalid_payload_entries_are_ignored(self) -> None:
        """Des payloads mal formés ne doivent pas produire de trigger."""
        rules = _trigger_rules()
        state = GameState.new_two_player()
        state.record_engine_event(
            EventType.OBJECT_RELOCATED,
            (
                ("object_id", -1),
                ("from_zone", "BATTLEFIELD"),
                ("to_zone", "GRAVEYARD"),
                ("from_player", 7),
                ("to_player", 7),
            ),
        )
        tm = TurnManager(state, rules=rules)
        tm.pass_priority()
        assert len(state.pending_triggers) == 0

    def test_unknown_effect_raises_on_resolution(self) -> None:
        """Un effet non supporté lève une erreur explicite à la résolution."""
        bad_rules = InMemoryCardCatalogAdapter(
            frozenset({"odd"}),
            creature_keys=frozenset({"odd"}),
            triggered_abilities_by_key={
                "odd": (
                    TriggeredAbilityDefinition(
                        ability_key="odd_upkeep",
                        trigger_kind="begin_step",
                        trigger_step="UPKEEP",
                        trigger_step_scope="you",
                        effect_kind="draw_cards",
                        amount=1,
                    ),
                )
            },
            creature_power_toughness_by_key={"odd": (1, 1)},
        )
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.UPKEEP))
        _register_permanent(state, 0, "odd")
        tm = TurnManager(state, rules=bad_rules)
        tm.open_current_step()
        # draw_cards est supporté ; force la branche d'erreur via monkey patch indirect:
        # on altère la définition attachée côté vue pour un effet invalide.
        stack_id = state.stack_zone.object_ids()[-1]
        view = state.get_triggered_ability_view(stack_id)
        assert view is not None

        class _BrokenDefinition:
            ability_key = "odd_upkeep"
            effect_kind = "unknown_effect"
            amount = 1
            target_kind = "none"

        # Conserve la forme de vue mais injecte une définition invalide.
        state.detach_triggered_ability_view(stack_id)
        state.attach_triggered_ability_view(
            stack_id,
            type(view)(
                ability_object_id=view.ability_object_id,
                pending_trigger_id=view.pending_trigger_id,
                controller_player_index=view.controller_player_index,
                source_object_id=view.source_object_id,
                source_catalog_key=view.source_catalog_key,
                ability_definition=_BrokenDefinition(),  # type: ignore[arg-type]
                targets=view.targets,
            ),
        )
        tm.pass_priority()
        with pytest.raises(InvalidGameStateError, match="non supporté"):
            tm.pass_priority()
