"""Lancement de sorts : validation, paiement, pile et enregistrement :class:`StackObject`."""

from __future__ import annotations

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.spell_on_stack import SpellOnStack
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.illegal_game_action_error import IllegalGameActionError
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError
from baobab_mtg_rules_engine.stack.stack_object import StackObject
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget
from baobab_mtg_rules_engine.targeting.target_validator import TargetValidator


class SpellCastService:
    """Valide timing, coûts et cibles puis place le sort sur la pile avec sa vue métier."""

    def __init__(self, target_validator: TargetValidator | None = None) -> None:
        self._targets: TargetValidator = target_validator or TargetValidator()

    def cast_spell(
        self,
        state: GameState,
        rules: CardGameplayPort,
        *,
        caster_player_index: int,
        spell_hand_object_id: GameObjectId,
        targets: tuple[SimpleTarget, ...],
    ) -> GameObjectId:
        """Lance un sort depuis la main vers la pile.

        :return: Identifiant du ``SpellOnStack`` nouvellement créé sur la pile.
        :raises IllegalGameActionError: timing ou carte illégale.
        :raises InvalidGameStateError: zone ou mana incohérents.
        """
        loc = state.find_location(spell_hand_object_id)
        if loc.zone_type is not ZoneType.HAND or loc.player_index != caster_player_index:
            msg = "Le sort doit être en main du lanceur."
            raise InvalidGameStateError(msg, field_name="spell_hand_object_id")
        card = state.get_object(spell_hand_object_id)
        if not isinstance(card, InGameCard) or isinstance(card, SpellOnStack):
            msg = "Seule une carte InGameCard en main (hors SpellOnStack) peut être lancée."
            raise IllegalGameActionError(msg, field_name="spell_hand_object_id")
        catalog_key = card.card_reference.catalog_key
        self._assert_cast_timing(state, rules, caster_player_index, catalog_key)
        cost = rules.spell_generic_mana_cost(catalog_key)
        if cost < 0:
            msg = "Coût de sort invalide."
            raise InvalidGameStateError(msg, field_name="generic_mana_cost")
        if state.players[caster_player_index].floating_mana < cost:
            msg = "Mana flottant insuffisant pour lancer ce sort."
            raise InvalidGameStateError(msg, field_name="floating_mana")
        self._targets.validate_at_cast(
            state,
            rules,
            caster_player_index=caster_player_index,
            spell_catalog_key=catalog_key,
            targets=targets,
        )
        stack_id = state.apply_cast_spell_hand_to_stack(
            caster_player_index,
            spell_hand_object_id,
            generic_mana_cost=cost,
        )
        view = StackObject(
            spell_object_id=stack_id,
            controller_player_index=caster_player_index,
            catalog_key=catalog_key,
            targets=targets,
        )
        state.attach_stack_object_view(stack_id, view)
        return stack_id

    def _assert_cast_timing(
        self,
        state: GameState,
        rules: CardGameplayPort,
        acting: int,
        catalog_key: str,
    ) -> None:
        is_instant = rules.is_instant_speed_spell_catalog_key(catalog_key)
        if is_instant:
            return
        is_sorcery_speed = rules.is_sorcery_speed_spell_catalog_key(catalog_key)
        is_creature_spell = rules.is_creature_spell_catalog_key(catalog_key)
        if is_sorcery_speed or is_creature_spell:
            if not self._sorcery_like_window(state, acting):
                msg = "Ce sort à vitesse rituelle requiert la principale active et une pile vide."
                raise IllegalGameActionError(msg, field_name="spell_hand_object_id")
            return
        msg = "Sort non classé comme rituel, créature ou éphémère dans le périmètre supporté."
        raise IllegalGameActionError(msg, field_name="spell_hand_object_id")

    def _sorcery_like_window(self, state: GameState, acting: int) -> bool:
        if state.turn_state.active_player_index != acting:
            return False
        if state.turn_state.step not in (Step.MAIN_PRECOMBAT, Step.MAIN_POSTCOMBAT):
            return False
        return len(state.stack_zone.object_ids()) == 0
