"""Résolution des capacités déclenchées simples avec fizzle ciblé."""

# Le contrôle de légalité des cibles garde des retours explicites par branche.
# pylint: disable=too-many-return-statements

from __future__ import annotations

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.triggered_ability_stack_object import (
    TriggeredAbilityStackObject,
)
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError


class TriggeredAbilityResolutionService:
    """Résout une capacité déclenchée du sommet de la pile."""

    def resolve_top(self, state: GameState, rules: CardGameplayPort) -> None:
        """Résout la capacité déclenchée au sommet de la pile.

        :raises InvalidGameStateError: si le sommet n'est pas une capacité déclenchée.
        """
        stack_ids = state.stack_zone.object_ids()
        if not stack_ids:
            msg = "La pile est vide : aucune capacité déclenchée à résoudre."
            raise InvalidGameStateError(msg, field_name="stack")
        top_id = stack_ids[-1]
        view = state.get_triggered_ability_view(top_id)
        if view is None:
            msg = "Vue de capacité déclenchée absente pour le sommet de pile."
            raise InvalidGameStateError(msg, field_name="stack")
        if not self._targets_legal_at_resolution(state, rules, view):
            state.remove_object_from_stack(top_id)
            state.record_engine_event(
                EventType.TRIGGER_FIZZLED,
                (
                    ("stack_object_id", top_id.value),
                    ("pending_trigger_id", view.pending_trigger_id),
                    ("ability_key", view.ability_definition.ability_key),
                    ("reason", "illegal_target_at_resolution"),
                ),
            )
            return
        self._apply_effect(state, view)
        state.remove_object_from_stack(top_id)
        state.record_engine_event(
            EventType.TRIGGER_RESOLVED,
            (
                ("stack_object_id", top_id.value),
                ("pending_trigger_id", view.pending_trigger_id),
                ("ability_key", view.ability_definition.ability_key),
            ),
        )

    def _targets_legal_at_resolution(
        self,
        state: GameState,
        rules: CardGameplayPort,
        view: TriggeredAbilityStackObject,
    ) -> bool:
        target_kind = view.ability_definition.target_kind
        if target_kind == "none":
            return len(view.targets) == 0
        if len(view.targets) != 1:
            return False
        target = view.targets[0]
        if target_kind == "player":
            return target.player_index is not None and target.player_index in (0, 1)
        if target_kind == "creature":
            if target.permanent_object_id is None:
                return False
            try:
                loc = state.find_location(target.permanent_object_id)
            except InvalidGameStateError:
                return False
            if loc.zone_type is not ZoneType.BATTLEFIELD:
                return False
            obj = state.get_object(target.permanent_object_id)
            if not isinstance(obj, Permanent):
                return False
            return rules.is_creature_catalog_key(obj.card_reference.catalog_key)
        return False

    def _apply_effect(
        self,
        state: GameState,
        view: TriggeredAbilityStackObject,
    ) -> None:
        definition = view.ability_definition
        amount = definition.amount
        if amount <= 0:
            return
        effect = definition.effect_kind
        if effect == "damage_opponent":
            self._resolve_damage_opponent(state, view, amount)
            return
        if effect == "damage_player":
            self._resolve_damage_player(state, view, amount)
            return
        if effect == "destroy_target_creature":
            self._resolve_destroy_target_creature(state, view)
            return
        if effect == "draw_cards":
            self._resolve_draw_cards(state, view, amount)
            return
        msg = f"Effet déclenché non supporté: {effect!r}."
        raise InvalidGameStateError(msg, field_name="effect_kind")

    def _resolve_damage_opponent(
        self,
        state: GameState,
        view: TriggeredAbilityStackObject,
        amount: int,
    ) -> None:
        target_player = 1 - view.controller_player_index
        self._damage_player(state, target_player, amount)

    def _resolve_damage_player(
        self,
        state: GameState,
        view: TriggeredAbilityStackObject,
        amount: int,
    ) -> None:
        target = view.targets[0]
        player_index = target.player_index
        if player_index is None:
            msg = "Effet de dégâts joueur sans cible joueur."
            raise InvalidGameStateError(msg, field_name="targets")
        self._damage_player(state, player_index, amount)

    def _resolve_destroy_target_creature(
        self,
        state: GameState,
        view: TriggeredAbilityStackObject,
    ) -> None:
        target = view.targets[0]
        creature_id = target.permanent_object_id
        if creature_id is None:
            msg = "Effet de destruction sans cible créature."
            raise InvalidGameStateError(msg, field_name="targets")
        loc = state.find_location(creature_id)
        if loc.player_index is None:
            msg = "La cible créature doit appartenir à un joueur."
            raise InvalidGameStateError(msg, field_name="targets")
        state.relocate_preserving_identity(
            creature_id,
            ZoneLocation(loc.player_index, ZoneType.GRAVEYARD),
        )
        state.record_engine_event(
            EventType.CREATURE_DESTROYED,
            (
                ("object_id", creature_id.value),
                ("owner_player_index", loc.player_index),
                ("reason", "triggered_ability"),
            ),
        )

    def _resolve_draw_cards(
        self,
        state: GameState,
        view: TriggeredAbilityStackObject,
        amount: int,
    ) -> None:
        # Le noyau supporte uniquement la pioche positive explicite.
        state.draw_cards_from_library_to_hand(view.controller_player_index, amount)
        state.record_engine_event(
            EventType.TURN_DRAW_PERFORMED,
            (
                ("player_index", view.controller_player_index),
                ("count", amount),
                ("source", "triggered_ability"),
            ),
        )

    def _damage_player(self, state: GameState, player_index: int, amount: int) -> None:
        state.players[player_index].apply_damage(amount)
        state.record_engine_event(
            EventType.PLAYER_DAMAGED,
            (
                ("player_index", player_index),
                ("amount", amount),
                ("source", "triggered_ability"),
            ),
        )
