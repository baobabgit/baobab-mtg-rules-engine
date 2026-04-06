"""Actions basées sur l'état (ABS) minimales pour le duel."""

from __future__ import annotations

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError


class StateBasedActionService:
    """Applique des ABS simples : destruction létale, défaite par points de vie."""

    _MAX_SBA_ROUNDS: int = 64

    def apply_all(self, state: GameState, rules: CardGameplayPort) -> None:
        """Boucle jusqu'à stabilité : créatures létales vers défausse, puis PV des joueurs.

        Deux joueurs à 0 PV ou moins : match nul déterministe.

        :raises InvalidGameStateError: si la boucle ABS ne stabilise pas.
        """
        if state.is_game_finished:
            return
        for _ in range(self._MAX_SBA_ROUNDS):
            if state.is_game_finished:
                return
            destroyed = self._destroy_lethal_creatures(state, rules)
            life_checked = self._apply_player_life_defeats(state)
            if not destroyed and not life_checked:
                return
        msg = "La boucle d'actions basées sur l'état n'a pas convergé."
        raise InvalidGameStateError(msg, field_name="state")

    def _destroy_lethal_creatures(self, state: GameState, rules: CardGameplayPort) -> bool:
        """Détruit les créatures dont les blessures marquées couvrent l'endurance."""
        to_destroy: list[tuple[GameObjectId, int]] = []
        for player in state.players:
            for oid in player.zone(ZoneType.BATTLEFIELD).object_ids():
                obj = state.get_object(oid)
                if not isinstance(obj, Permanent):
                    continue
                key = obj.card_reference.catalog_key
                if not rules.is_creature_catalog_key(key):
                    continue
                tough = rules.creature_toughness(key)
                if obj.marked_damage >= tough > 0:
                    to_destroy.append((oid, player.player_index))
        to_destroy.sort(key=lambda t: t[0].value)
        for oid, owner in to_destroy:
            grave = ZoneLocation(owner, ZoneType.GRAVEYARD)
            state.relocate_preserving_identity(oid, grave)
            state.record_engine_event(
                EventType.CREATURE_DESTROYED,
                (
                    ("object_id", oid.value),
                    ("owner_player_index", owner),
                    ("reason", "lethal_damage"),
                ),
            )
        return len(to_destroy) > 0

    def _apply_player_life_defeats(self, state: GameState) -> bool:
        """Enregistre défaite ou match nul selon les points de vie."""
        if state.is_game_finished:
            return False
        p0 = state.players[0].life_total <= 0
        p1 = state.players[1].life_total <= 0
        if p0 and p1:
            state.record_draw_game()
            return True
        if p0:
            state.record_player_defeat(0, reason="life")
            return True
        if p1:
            state.record_player_defeat(1, reason="life")
            return True
        return False
