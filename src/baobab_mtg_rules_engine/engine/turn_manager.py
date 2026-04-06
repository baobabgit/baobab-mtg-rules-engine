"""Orchestrateur : enchaînement des étapes, priorité et effets obligatoires du tour."""

from __future__ import annotations

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.combat.combat_service import CombatService
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.engine.state_based_action_service import StateBasedActionService
from baobab_mtg_rules_engine.exceptions.insufficient_library_error import InsufficientLibraryError
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError
from baobab_mtg_rules_engine.engine.null_priority_action_legality_port import (
    NullPriorityActionLegalityPort,
)
from baobab_mtg_rules_engine.engine.priority_action_legality_port import PriorityActionLegalityPort
from baobab_mtg_rules_engine.engine.priority_manager import PriorityManager
from baobab_mtg_rules_engine.engine.step_transition_service import StepTransitionService


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
        self._priority: PriorityManager = PriorityManager(state)
        self._steps: StepTransitionService = StepTransitionService()

    def open_current_step(self) -> None:
        """Applique les effets d'entrée de l'étape courante et prépare la priorité si besoin."""
        step = self._state.turn_state.step
        if step is Step.BEGIN_COMBAT:
            self._state.turn_engine_begin_combat_declarations()
        if step is Step.COMBAT_DAMAGE:
            self._emit_step_entered()
            if self._rules is not None:
                CombatService().resolve_combat_damage_step(self._state, self._rules)
                StateBasedActionService().apply_all(self._state, self._rules)
            self._priority.assign_to_active_player()
            self._emit_priority_assigned()
            return
        if step is Step.UNTAP:
            self._emit_step_entered()
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
            self._priority.assign_to_active_player()
            self._emit_priority_assigned()
            return
        self._emit_step_entered()
        self._priority.assign_to_active_player()
        self._emit_priority_assigned()

    def pass_priority(self) -> None:
        """Enregistre une passe du joueur qui détient actuellement la priorité."""
        passer = self._state.priority_player_index
        self._legality.assert_legal_priority_window(self._state, passer)
        should_advance = self._priority.process_priority_pass()
        self._state.record_engine_event(
            EventType.PRIORITY_PASSED,
            (("player_index", passer),),
        )
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
