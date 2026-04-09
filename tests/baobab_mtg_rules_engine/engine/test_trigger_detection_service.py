"""Tests unitaires pour :class:`TriggerDetectionService`."""

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.triggered_ability_definition import TriggeredAbilityDefinition
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.engine.trigger_detection_service import TriggerDetectionService


def _rules() -> InMemoryCardCatalogAdapter:
    return InMemoryCardCatalogAdapter(
        frozenset({"sage", "axeman", "caster", "striker"}),
        creature_keys=frozenset({"sage", "axeman", "striker"}),
        creature_spell_keys=frozenset({"sage"}),
        sorcery_spell_keys=frozenset({"caster"}),
        spell_mana_cost_by_key={"sage": 1, "caster": 1},
        triggered_abilities_by_key={
            "sage": (
                TriggeredAbilityDefinition(
                    ability_key="sage_etb",
                    trigger_kind="etb_self",
                    effect_kind="damage_opponent",
                    amount=1,
                ),
            ),
            "axeman": (
                TriggeredAbilityDefinition(
                    ability_key="axeman_dies",
                    trigger_kind="dies_self",
                    effect_kind="damage_opponent",
                    amount=1,
                ),
            ),
            "caster": (
                TriggeredAbilityDefinition(
                    ability_key="caster_cast",
                    trigger_kind="cast_self",
                    effect_kind="damage_opponent",
                    amount=1,
                ),
            ),
            "striker": (
                TriggeredAbilityDefinition(
                    ability_key="striker_hit",
                    trigger_kind="combat_damage_to_player_self",
                    effect_kind="damage_opponent",
                    amount=1,
                ),
                TriggeredAbilityDefinition(
                    ability_key="upkeep_ping",
                    trigger_kind="begin_step",
                    trigger_step="UPKEEP",
                    trigger_step_scope="you",
                    effect_kind="damage_opponent",
                    amount=1,
                ),
                TriggeredAbilityDefinition(
                    ability_key="draw_ping",
                    trigger_kind="draw_you",
                    effect_kind="damage_opponent",
                    amount=1,
                ),
            ),
        },
        creature_power_toughness_by_key={"sage": (1, 1), "axeman": (2, 2), "striker": (2, 2)},
    )


def _register_permanent(state: GameState, player: int, key: str) -> None:
    oid = state.issue_object_id()
    state.register_object_at(
        Permanent(oid, CardReference(key)),
        ZoneLocation(player, ZoneType.BATTLEFIELD),
    )


class TestTriggerDetectionService:
    """Détection incrémentale sur événements et chemin begin-step fallback."""

    def test_scan_new_events_detects_all_supported_trigger_kinds(self) -> None:
        """ETB, dies, cast, draw et combat-damage-to-player sont détectés."""
        rules = _rules()
        state = GameState.new_two_player()
        detector = TriggerDetectionService()

        _register_permanent(state, 0, "sage")
        _register_permanent(state, 0, "axeman")
        _register_permanent(state, 0, "striker")

        hand_id = state.issue_object_id()
        state.register_object_at(
            InGameCard(hand_id, CardReference("caster")),
            ZoneLocation(0, ZoneType.HAND),
        )
        state.players[0].add_floating_mana(2)
        state.apply_cast_spell_hand_to_stack(0, hand_id, generic_mana_cost=1)
        state.relocate_preserving_identity(
            state.players[0].zone(ZoneType.BATTLEFIELD).object_ids()[1],
            ZoneLocation(0, ZoneType.GRAVEYARD),
        )
        state.record_engine_event(
            EventType.TURN_DRAW_PERFORMED,
            (("player_index", 0), ("count", 1)),
        )
        attacker_id = state.players[0].zone(ZoneType.BATTLEFIELD).object_ids()[-1]
        state.record_engine_event(
            EventType.COMBAT_DAMAGE_ASSIGNED,
            (
                ("attacker_id", attacker_id.value),
                ("target", "player"),
                ("defending_player_index", 1),
                ("amount", 2),
            ),
        )

        last_before_scan = state.events[-1].sequence
        latest = detector.scan_new_events(state, rules, from_sequence_exclusive=0)
        # ``latest`` est la dernière séquence d'événement analysée en entrée
        # (avant ajout des événements TRIGGER_* par la détection elle-même).
        assert latest == last_before_scan
        assert len(state.pending_triggers) >= 4
        queued_keys = {p.ability_definition.ability_key for p in state.pending_triggers}
        assert "sage_etb" not in queued_keys
        assert "axeman_dies" in queued_keys
        assert "caster_cast" in queued_keys
        assert "draw_ping" in queued_keys
        assert "striker_hit" in queued_keys

    def test_detect_begin_step_from_state_queues_without_step_event(self) -> None:
        """Le fallback begin-step depuis l'état détecte correctement sans TURN_STEP_ENTERED."""
        rules = _rules()
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.UPKEEP))
        _register_permanent(state, 0, "striker")

        detector = TriggerDetectionService()
        detector.detect_begin_step_from_state(state, rules)
        assert len(state.pending_triggers) == 1
        queued = state.pending_triggers[0]
        assert queued.ability_definition.ability_key == "upkeep_ping"
        assert queued.trigger_event_sequence == -1
