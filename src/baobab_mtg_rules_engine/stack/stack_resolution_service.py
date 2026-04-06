"""Résolution du sommet de la pile (LIFO) avec fizzle si cibles illégales."""

from __future__ import annotations

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError
from baobab_mtg_rules_engine.stack.stack_object import StackObject
from baobab_mtg_rules_engine.targeting.target_validator import TargetValidator


class StackResolutionService:
    """Résout le sommet : fizzle si les cibles sont illégales, sinon effet simple."""

    def __init__(self, target_validator: TargetValidator | None = None) -> None:
        self._targets: TargetValidator = target_validator or TargetValidator()

    def resolve_top(self, state: GameState, rules: CardGameplayPort) -> None:
        """Résout l'objet au sommet de la pile (dernier empilé).

        :raises InvalidGameStateError: si la pile est vide ou les métadonnées manquent.
        """
        stack_ids = state.stack_zone.object_ids()
        if not stack_ids:
            msg = "La pile est vide : aucune résolution possible."
            raise InvalidGameStateError(msg, field_name="stack")
        top_id = stack_ids[-1]
        view = state.get_stack_object_view(top_id)
        if view is None:
            msg = "Vue StackObject absente pour le sort au sommet de la pile."
            raise InvalidGameStateError(msg, field_name="stack")
        key = view.catalog_key
        if not self._targets.all_targets_still_legal_at_resolution(
            state,
            rules,
            spell_catalog_key=key,
            targets=view.targets,
        ):
            self._fizzle_spell(state, top_id, view)
            return
        self._resolve_success(state, rules, top_id, view)

    def _fizzle_spell(self, state: GameState, top_id: GameObjectId, view: StackObject) -> None:
        state.detach_stack_object_view(top_id)
        grave = ZoneLocation(view.controller_player_index, ZoneType.GRAVEYARD)
        state.migrate_in_game_card_as_new_instance(top_id, target=grave, new_kind=InGameCard)
        state.record_engine_event(
            EventType.SPELL_FIZZLED,
            (
                ("spell_object_id", top_id.value),
                ("catalog_key", view.catalog_key),
            ),
        )

    def _resolve_success(
        self,
        state: GameState,
        rules: CardGameplayPort,
        top_id: GameObjectId,
        view: StackObject,
    ) -> None:
        key = view.catalog_key
        state.detach_stack_object_view(top_id)
        if rules.is_creature_spell_catalog_key(key):
            battlefield = ZoneLocation(view.controller_player_index, ZoneType.BATTLEFIELD)
            state.migrate_in_game_card_as_new_instance(
                top_id,
                target=battlefield,
                new_kind=Permanent,
            )
            state.record_engine_event(
                EventType.SPELL_RESOLVED,
                (
                    ("spell_object_id", top_id.value),
                    ("catalog_key", key),
                    ("resolution", "creature"),
                ),
            )
            return
        damage = rules.spell_damage_to_player_amount(key)
        if damage > 0:
            if len(view.targets) != 1 or view.targets[0].player_index is None:
                msg = "Sort de dégâts joueur : une cible joueur unique est requise."
                raise InvalidGameStateError(msg, field_name="targets")
            player_index = view.targets[0].player_index
            state.players[player_index].apply_damage(damage)
            state.record_engine_event(
                EventType.PLAYER_DAMAGED,
                (
                    ("player_index", player_index),
                    ("amount", damage),
                ),
            )
            grave = ZoneLocation(view.controller_player_index, ZoneType.GRAVEYARD)
            state.migrate_in_game_card_as_new_instance(top_id, target=grave, new_kind=InGameCard)
            state.record_engine_event(
                EventType.SPELL_RESOLVED,
                (
                    ("spell_object_id", top_id.value),
                    ("catalog_key", key),
                    ("resolution", "damage_player"),
                ),
            )
            return
        grave = ZoneLocation(view.controller_player_index, ZoneType.GRAVEYARD)
        state.migrate_in_game_card_as_new_instance(top_id, target=grave, new_kind=InGameCard)
        state.record_engine_event(
            EventType.SPELL_RESOLVED,
            (
                ("spell_object_id", top_id.value),
                ("catalog_key", key),
                ("resolution", "graveyard"),
            ),
        )
