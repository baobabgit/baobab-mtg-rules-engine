"""Orchestrateur : enchaînement des étapes, priorité et effets obligatoires du tour."""

from __future__ import annotations

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.combat.combat_service import CombatService
from baobab_mtg_rules_engine.domain.ability_on_stack import AbilityOnStack
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.pending_triggered_ability import PendingTriggeredAbility
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.triggered_ability_stack_object import (
    TriggeredAbilityStackObject,
)
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.engine.trigger_detection_service import TriggerDetectionService
from baobab_mtg_rules_engine.engine.state_based_action_service import StateBasedActionService
from baobab_mtg_rules_engine.exceptions.insufficient_library_error import InsufficientLibraryError
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError
from baobab_mtg_rules_engine.engine.null_priority_action_legality_port import (
    NullPriorityActionLegalityPort,
)
from baobab_mtg_rules_engine.engine.priority_action_legality_port import PriorityActionLegalityPort
from baobab_mtg_rules_engine.engine.priority_manager import PriorityManager
from baobab_mtg_rules_engine.engine.step_transition_service import StepTransitionService
from baobab_mtg_rules_engine.stack.stack_resolution_service import StackResolutionService
from baobab_mtg_rules_engine.stack.triggered_ability_resolution_service import (
    TriggeredAbilityResolutionService,
)
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget


class TurnManager:
    """Boucle de tour en duel : phases/étapes, priorité, saut de pioche initial.

    Les étapes sans fenêtre de priorité dans ce périmètre : le dégagement enchaîne
    vers l'entretien ; le nettoyage vide le mana résiduel et passe au tour suivant.

    :param state: État de partie à deux joueurs.
    :param legality: Contrôle exécuté avant chaque passe (aucune mutation en cas d'échec).
    :param rules: Si fourni, résolution des blessures de combat et ABS après dégâts de combat.
    """

    def __init__(
        self,
        state: GameState,
        *,
        legality: PriorityActionLegalityPort | None = None,
        rules: CardGameplayPort | None = None,
    ) -> None:
        self._state: GameState = state
        self._legality: PriorityActionLegalityPort = legality or NullPriorityActionLegalityPort()
        self._rules: CardGameplayPort | None = rules
        self._priority: PriorityManager = PriorityManager(
            state,
            close_non_empty_window=rules is not None,
        )
        self._steps: StepTransitionService = StepTransitionService()
        self._trigger_detection: TriggerDetectionService = TriggerDetectionService()
        self._spell_resolution: StackResolutionService = StackResolutionService()
        self._trigger_resolution: TriggeredAbilityResolutionService = (
            TriggeredAbilityResolutionService()
        )
        if self._rules is not None and self._state.events:
            self._state.mark_trigger_scan_sequence(self._state.events[-1].sequence)

    def open_current_step(self) -> None:  # pylint: disable=too-many-return-statements
        """Applique les effets d'entrée de l'étape courante et prépare la priorité si besoin."""
        step = self._state.turn_state.step
        if step is Step.BEGIN_COMBAT:
            self._state.turn_engine_begin_combat_declarations()
        if step is Step.COMBAT_DAMAGE:
            self._emit_step_entered()
            if self._rules is not None:
                CombatService().resolve_combat_damage_step(self._state, self._rules)
                StateBasedActionService().apply_all(self._state, self._rules)
                self._detect_and_queue_triggers_from_new_events()
                if self._stack_pending_triggers_if_any():
                    return
            self._priority.assign_to_active_player()
            self._emit_priority_assigned()
            return
        if step is Step.UNTAP:
            self._emit_step_entered()
            if self._rules is not None:
                self._detect_and_queue_triggers_from_new_events()
            self._replace_step_only(Step.UPKEEP)
            self.open_current_step()
            return
        if step is Step.CLEANUP:
            self._emit_step_entered()
            self._state.clear_all_marked_damage_on_battlefield()
            self._cleanup_floating_mana()
            self._roll_turn_after_cleanup()
            self.open_current_step()
            return
        if step is Step.DRAW:
            self._emit_step_entered()
            self._resolve_draw_step()
            if self._rules is not None:
                self._detect_and_queue_triggers_from_new_events()
                if self._stack_pending_triggers_if_any():
                    return
            self._priority.assign_to_active_player()
            self._emit_priority_assigned()
            return
        self._emit_step_entered()
        if self._rules is not None:
            self._detect_and_queue_triggers_from_new_events()
            if self._stack_pending_triggers_if_any():
                return
        self._priority.assign_to_active_player()
        self._emit_priority_assigned()

    def pass_priority(self) -> None:
        """Enregistre une passe du joueur qui détient actuellement la priorité."""
        if self._rules is not None:
            self._detect_and_queue_triggers_from_new_events()
            if self._stack_pending_triggers_if_any():
                return
        passer = self._state.priority_player_index
        self._legality.assert_legal_priority_window(self._state, passer)
        should_advance = self._priority.process_priority_pass()
        self._state.record_engine_event(
            EventType.PRIORITY_PASSED,
            (("player_index", passer),),
        )
        if (
            should_advance
            and self._rules is not None
            and len(self._state.stack_zone.object_ids()) > 0
        ):
            self._resolve_top_stack_object()
            self._run_sba_and_triggers_loop()
            return
        if should_advance:
            self._advance_step_after_priority_window()

    def _advance_step_after_priority_window(self) -> None:
        ts = self._state.turn_state
        nxt = self._steps.successor_step(ts.step)
        if nxt is None:
            msg = "Cette étape ne se termine pas par passes de priorité dans ce moteur."
            raise InvalidGameStateError(msg, field_name="step")
        self._state.replace_turn_state(
            TurnState(ts.active_player_index, ts.turn_number, nxt),
        )
        self._state.record_engine_event(
            EventType.TURN_STEP_ADVANCED,
            (
                ("from_step", ts.step.name),
                ("to_step", nxt.name),
                ("active_player", ts.active_player_index),
            ),
        )
        self.open_current_step()

    def _roll_turn_after_cleanup(self) -> None:
        ts = self._state.turn_state
        new_ts = self._steps.turn_state_after_cleanup(ts)
        self._state.replace_turn_state(new_ts)
        self._state.turn_engine_reset_turn_resource_counters()
        self._state.record_engine_event(
            EventType.TURN_ROLLED_TO_NEXT_PLAYER,
            (
                ("previous_active", ts.active_player_index),
                ("new_active", new_ts.active_player_index),
                ("turn_number", new_ts.turn_number),
            ),
        )

    def _replace_step_only(self, new_step: Step) -> None:
        ts = self._state.turn_state
        self._state.replace_turn_state(TurnState(ts.active_player_index, ts.turn_number, new_step))

    def _emit_step_entered(self) -> None:
        ts = self._state.turn_state
        self._state.record_engine_event(
            EventType.TURN_STEP_ENTERED,
            (
                ("step", ts.step.name),
                ("phase", ts.phase.name),
                ("active_player", ts.active_player_index),
                ("turn_number", ts.turn_number),
            ),
        )

    def _emit_priority_assigned(self) -> None:
        self._state.record_engine_event(
            EventType.PRIORITY_ASSIGNED,
            (
                ("player_index", self._state.priority_player_index),
                ("step", self._state.turn_state.step.name),
            ),
        )

    def _resolve_draw_step(self) -> None:
        ts = self._state.turn_state
        if self._should_skip_first_draw_of_duel():
            self._state.record_engine_event(
                EventType.TURN_DRAW_STEP_SKIPPED_FIRST_DUEL_TURN,
                (
                    ("active_player", ts.active_player_index),
                    ("turn_number", ts.turn_number),
                ),
            )
            return
        try:
            drawn = self._state.draw_cards_from_library_to_hand(ts.active_player_index, 1)
        except InsufficientLibraryError:
            self._state.record_player_defeat(ts.active_player_index, reason="library")
            return
        self._state.record_engine_event(
            EventType.TURN_DRAW_PERFORMED,
            (
                ("player_index", ts.active_player_index),
                ("count", len(drawn)),
            ),
        )

    def _should_skip_first_draw_of_duel(self) -> bool:
        ts = self._state.turn_state
        return (
            ts.turn_number == 1
            and ts.step is Step.DRAW
            and ts.active_player_index == self._state.duel_first_player_index
        )

    def _cleanup_floating_mana(self) -> None:
        for idx, player in enumerate(self._state.players):
            if player.floating_mana > 0:
                player.clear_floating_mana()
                self._state.record_engine_event(
                    EventType.FLOATING_MANA_CLEARED,
                    (("player_index", idx),),
                )

    def _detect_and_queue_triggers_from_new_events(self) -> None:
        if self._rules is None:
            return
        last_scanned = self._state.trigger_scan_sequence
        latest = self._trigger_detection.scan_new_events(
            self._state,
            self._rules,
            from_sequence_exclusive=last_scanned,
        )
        self._state.mark_trigger_scan_sequence(latest)

    def _stack_pending_triggers_if_any(self) -> bool:
        if len(self._state.pending_triggers) == 0:
            return False
        queued = self._state.pop_all_pending_triggers()
        active = self._state.turn_state.active_player_index
        ordered = sorted(
            queued,
            key=lambda p: (
                0 if p.controller_player_index == active else 1,
                p.controller_player_index,
                p.pending_trigger_id,
            ),
        )
        for pending in ordered:
            ability_object_id = self._state.issue_object_id()
            ability = AbilityOnStack(
                ability_object_id,
                source_object_id=pending.source_object_id,
                ability_key=pending.ability_definition.ability_key,
            )
            self._state.register_object_at(ability, ZoneLocation(None, ZoneType.STACK))
            targets = self._default_trigger_targets(pending)
            view = TriggeredAbilityStackObject(
                ability_object_id=ability_object_id,
                pending_trigger_id=pending.pending_trigger_id,
                controller_player_index=pending.controller_player_index,
                source_object_id=pending.source_object_id,
                source_catalog_key=pending.source_catalog_key,
                ability_definition=pending.ability_definition,
                targets=targets,
            )
            self._state.attach_triggered_ability_view(ability_object_id, view)
            self._state.record_engine_event(
                EventType.TRIGGER_STACKED,
                (
                    ("pending_trigger_id", pending.pending_trigger_id),
                    ("stack_object_id", ability_object_id.value),
                    ("controller_player_index", pending.controller_player_index),
                    ("ability_key", pending.ability_definition.ability_key),
                ),
            )
        self._priority.assign_to_active_player()
        self._emit_priority_assigned()
        return True

    def _default_trigger_targets(
        self,
        pending: PendingTriggeredAbility,
    ) -> tuple[SimpleTarget, ...]:
        p = pending
        target_kind = p.ability_definition.target_kind
        if target_kind == "none":
            return ()
        if target_kind == "player":
            return (SimpleTarget.for_player(1 - p.controller_player_index),)
        if target_kind == "creature":
            creature_ids: list[int] = []
            for player in self._state.players:
                for oid in player.zone(ZoneType.BATTLEFIELD).object_ids():
                    obj = self._state.get_object(oid)
                    if not isinstance(obj, Permanent):
                        continue
                    if self._rules is None:
                        continue
                    catalog_key = obj.card_reference.catalog_key
                    if self._rules.is_creature_catalog_key(catalog_key):
                        creature_ids.append(oid.value)
            creature_ids.sort()
            if creature_ids:
                return (SimpleTarget.for_permanent(GameObjectId(creature_ids[0])),)
            return ()
        return ()

    def _resolve_top_stack_object(self) -> None:
        if self._rules is None:
            return
        stack_ids = self._state.stack_zone.object_ids()
        if not stack_ids:
            return
        top_id = stack_ids[-1]
        if self._state.get_triggered_ability_view(top_id) is not None:
            self._trigger_resolution.resolve_top(self._state, self._rules)
            return
        self._spell_resolution.resolve_top(self._state, self._rules)

    def _run_sba_and_triggers_loop(self) -> None:
        if self._rules is None:
            return
        StateBasedActionService().apply_all(self._state, self._rules)
        self._detect_and_queue_triggers_from_new_events()
        if self._stack_pending_triggers_if_any():
            return
        self._priority.assign_to_active_player()
        self._emit_priority_assigned()
