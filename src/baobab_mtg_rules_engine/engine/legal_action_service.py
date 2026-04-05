"""Calcul déterministe des actions légales et application après re-validation."""

from __future__ import annotations

from baobab_mtg_rules_engine.actions.activate_simple_ability_action import (
    ActivateSimpleAbilityAction,
)
from baobab_mtg_rules_engine.actions.cast_spell_action import CastSpellAction
from baobab_mtg_rules_engine.actions.declare_attacker_action import DeclareAttackerAction
from baobab_mtg_rules_engine.actions.declare_blocker_action import DeclareBlockerAction
from baobab_mtg_rules_engine.actions.game_action import GameAction
from baobab_mtg_rules_engine.actions.pass_priority_action import PassPriorityAction
from baobab_mtg_rules_engine.actions.play_land_action import PlayLandAction
from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.spell_on_stack import SpellOnStack
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.engine.turn_manager import TurnManager
from baobab_mtg_rules_engine.exceptions.illegal_game_action_error import IllegalGameActionError

_PASS_SINGLETON = PassPriorityAction()


class LegalActionService:
    """Liste les actions supportées à un instant donné et les applique sans court-circuit."""

    def compute_legal_actions(
        self,
        state: GameState,
        rules: CardGameplayPort,
        acting_player_index: int,
    ) -> tuple[GameAction, ...]:
        """Construit la liste triée des actions légales pour le joueur indiqué.

        :raises IllegalGameActionError: si le joueur ne détient pas la priorité.
        """
        self._assert_holding_priority(state, acting_player_index)
        actions: list[GameAction] = [_PASS_SINGLETON]
        actions.extend(self._legal_lands(state, rules, acting_player_index))
        for oid in self._legal_cast_spell_object_ids(state, rules, acting_player_index):
            actions.append(CastSpellAction(oid))
        actions.extend(self._legal_activations(state, rules, acting_player_index))
        actions.extend(self._legal_attackers(state, rules, acting_player_index))
        actions.extend(self._legal_blockers(state, rules, acting_player_index))
        actions.sort(key=lambda a: a.sort_key())
        return tuple(actions)

    def apply_action(  # pylint: disable=too-many-positional-arguments
        self,
        state: GameState,
        rules: CardGameplayPort,
        acting_player_index: int,
        action: GameAction,
        turn_manager: TurnManager,
    ) -> None:
        """Applique une action après contrôle d'appartenance à l'ensemble légal courant.

        :raises IllegalGameActionError: si l'action n'est pas légale ou la priorité est incorrecte.
        """
        self._assert_holding_priority(state, acting_player_index)
        legal = self.compute_legal_actions(state, rules, acting_player_index)
        if action not in legal:
            msg = "Action absente de l'ensemble légal courant."
            raise IllegalGameActionError(msg, field_name="action")
        if isinstance(action, PassPriorityAction):
            turn_manager.pass_priority()
        elif isinstance(action, PlayLandAction):
            state.apply_play_land(acting_player_index, action.land_object_id)
        elif isinstance(action, CastSpellAction):
            card = state.get_object(action.spell_object_id)
            if not isinstance(card, InGameCard) or isinstance(card, SpellOnStack):
                msg = (
                    "Le sort doit être une carte en main (représentation InGameCard) "
                    "avant résolution."
                )
                raise IllegalGameActionError(msg, field_name="spell_object_id")
            cost = rules.spell_generic_mana_cost(card.card_reference.catalog_key)
            state.apply_cast_spell_hand_to_stack(
                acting_player_index,
                action.spell_object_id,
                generic_mana_cost=cost,
            )
        elif isinstance(action, ActivateSimpleAbilityAction):
            state.apply_activate_simple_ability(
                acting_player_index,
                action.permanent_object_id,
                generic_mana_cost=action.generic_mana_cost,
            )
        elif isinstance(action, DeclareAttackerAction):
            state.apply_declare_attacker(
                state.turn_state.active_player_index,
                action.creature_object_id,
            )
        elif isinstance(action, DeclareBlockerAction):
            defending = 1 - state.turn_state.active_player_index
            state.apply_declare_blocker(
                defending,
                action.blocker_object_id,
                action.attacker_object_id,
            )
        else:
            msg = f"Type d'action non géré : {type(action)!r}."
            raise IllegalGameActionError(msg, field_name="action")

    def _assert_holding_priority(self, state: GameState, acting_player_index: int) -> None:
        if acting_player_index != state.priority_player_index:
            msg = "Seul le détenteur de la priorité peut agir ou consulter ces actions légales."
            raise IllegalGameActionError(msg, field_name="acting_player_index")

    def _stack_empty(self, state: GameState) -> bool:
        return len(state.stack_zone.object_ids()) == 0

    def _main_phase_active_player(self, state: GameState, acting: int) -> bool:
        return state.turn_state.active_player_index == acting and state.turn_state.step in (
            Step.MAIN_PRECOMBAT,
            Step.MAIN_POSTCOMBAT,
        )

    def _sorcery_timing_ok(self, state: GameState, acting: int) -> bool:
        return self._main_phase_active_player(state, acting) and self._stack_empty(state)

    def _legal_cast_spell_object_ids(
        self,
        state: GameState,
        rules: CardGameplayPort,
        acting: int,
    ) -> tuple[GameObjectId, ...]:
        """Identifiants en main lançables à vitesse rituelle et/ou instantanée (sans doublon)."""
        ordered: list[GameObjectId] = []
        hand = state.players[acting].zone(ZoneType.HAND).object_ids()
        for oid in sorted(hand, key=lambda x: x.value):
            obj = state.get_object(oid)
            if not isinstance(obj, InGameCard) or isinstance(obj, SpellOnStack):
                continue
            key = obj.card_reference.catalog_key
            is_sorcery_key = rules.is_sorcery_speed_spell_catalog_key(key)
            is_instant_key = rules.is_instant_speed_spell_catalog_key(key)
            if not is_sorcery_key and not is_instant_key:
                continue
            sorcery_ok = is_sorcery_key and self._sorcery_timing_ok(state, acting)
            instant_ok = is_instant_key
            if not sorcery_ok and not instant_ok:
                continue
            cost = rules.spell_generic_mana_cost(key)
            if state.players[acting].floating_mana < cost:
                continue
            ordered.append(oid)
        return tuple(ordered)

    def _legal_lands(
        self,
        state: GameState,
        rules: CardGameplayPort,
        acting: int,
    ) -> list[PlayLandAction]:
        if not self._sorcery_timing_ok(state, acting):
            return []
        if state.lands_played_this_turn >= 1:
            return []
        out: list[PlayLandAction] = []
        for oid in state.players[acting].zone(ZoneType.HAND).object_ids():
            obj = state.get_object(oid)
            if not isinstance(obj, InGameCard) or isinstance(obj, SpellOnStack):
                continue
            key = obj.card_reference.catalog_key
            if rules.is_land_catalog_key(key):
                out.append(PlayLandAction(oid))
        out.sort(key=lambda a: a.sort_key())
        return out

    def _legal_activations(
        self,
        state: GameState,
        rules: CardGameplayPort,
        acting: int,
    ) -> list[ActivateSimpleAbilityAction]:
        out: list[ActivateSimpleAbilityAction] = []
        for oid in state.players[acting].zone(ZoneType.BATTLEFIELD).object_ids():
            obj = state.get_object(oid)
            if not isinstance(obj, Permanent):
                continue
            key = obj.card_reference.catalog_key
            for cost in rules.simple_activated_ability_costs(key):
                if cost < 0:
                    continue
                if state.players[acting].floating_mana >= cost:
                    out.append(ActivateSimpleAbilityAction(oid, cost))
        out.sort(key=lambda a: a.sort_key())
        return out

    def _legal_attackers(
        self,
        state: GameState,
        rules: CardGameplayPort,
        acting: int,
    ) -> list[DeclareAttackerAction]:
        if state.turn_state.step is not Step.DECLARE_ATTACKERS:
            return []
        if acting != state.turn_state.active_player_index:
            return []
        if not self._stack_empty(state):
            return []
        ap = state.turn_state.active_player_index
        out: list[DeclareAttackerAction] = []
        for oid in state.players[ap].zone(ZoneType.BATTLEFIELD).object_ids():
            if oid in state.declared_attackers:
                continue
            obj = state.get_object(oid)
            if not isinstance(obj, Permanent):
                continue
            if rules.is_creature_catalog_key(obj.card_reference.catalog_key):
                out.append(DeclareAttackerAction(oid))
        out.sort(key=lambda a: a.sort_key())
        return out

    def _legal_blockers(
        self,
        state: GameState,
        rules: CardGameplayPort,
        acting: int,
    ) -> list[DeclareBlockerAction]:
        if state.turn_state.step is not Step.DECLARE_BLOCKERS:
            return []
        active = state.turn_state.active_player_index
        if acting == active:
            return []
        if not self._stack_empty(state):
            return []
        defender = acting
        used_blockers = {b for b, _ in state.declared_blocks}
        out: list[DeclareBlockerAction] = []
        for attacker_id in state.declared_attackers:
            for oid in state.players[defender].zone(ZoneType.BATTLEFIELD).object_ids():
                if oid in used_blockers:
                    continue
                obj = state.get_object(oid)
                if not isinstance(obj, Permanent):
                    continue
                if rules.is_creature_catalog_key(obj.card_reference.catalog_key):
                    out.append(DeclareBlockerAction(oid, attacker_id))
        out.sort(key=lambda a: a.sort_key())
        return out
