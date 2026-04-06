"""Résolution des blessures de combat (duel simplifié, un bloqueur par attaquant max)."""

from __future__ import annotations

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.illegal_game_action_error import IllegalGameActionError
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError


class CombatService:
    """Assigne les blessures de combat selon force/endurance catalogue."""

    def resolve_combat_damage_step(self, state: GameState, rules: CardGameplayPort) -> None:
        """Applique les dégâts de combat pour l'étape ``COMBAT_DAMAGE``.

        - Attaquant non bloqué : dégâts au joueur défenseur égaux à la force.
        - Avec un unique bloqueur : échange de dégâts entre les deux créatures.

        :raises InvalidGameStateError: si l'étape ou la pile est incohérente.
        :raises IllegalGameActionError: si plus d'un bloqueur par attaquant.
        """
        if state.is_game_finished:
            return
        if state.turn_state.step is not Step.COMBAT_DAMAGE:
            msg = "Les blessures de combat ne s'appliquent qu'à l'étape COMBAT_DAMAGE."
            raise InvalidGameStateError(msg, field_name="step")
        if len(state.stack_zone.object_ids()) != 0:
            msg = "La pile doit être vide pour résoudre les blessures de combat."
            raise InvalidGameStateError(msg, field_name="stack")
        active = state.turn_state.active_player_index
        defending = 1 - active
        blocks_by_attacker: dict[GameObjectId, list[GameObjectId]] = {}
        for blocker_id, attacker_id in state.declared_blocks:
            blocks_by_attacker.setdefault(attacker_id, []).append(blocker_id)
        for _, blockers in blocks_by_attacker.items():
            blockers.sort(key=lambda x: x.value)
            if len(blockers) > 1:
                msg = "Plus d'un bloqueur par attaquant : hors périmètre du moteur."
                raise IllegalGameActionError(msg, field_name="declared_blocks")
        for attacker_id in sorted(state.declared_attackers, key=lambda x: x.value):
            self._resolve_one_attacker(
                state,
                rules,
                attacker_id=attacker_id,
                defending_player_index=defending,
                blocks_by_attacker=blocks_by_attacker,
            )

    def _damage_player_from_unblocked_attacker(
        self,
        state: GameState,
        *,
        attacker_id: GameObjectId,
        defending_player_index: int,
        amount: int,
    ) -> None:
        state.players[defending_player_index].apply_damage(amount)
        state.record_engine_event(
            EventType.COMBAT_DAMAGE_ASSIGNED,
            (
                ("attacker_id", attacker_id.value),
                ("target", "player"),
                ("defending_player_index", defending_player_index),
                ("amount", amount),
            ),
        )
        state.record_engine_event(
            EventType.PLAYER_DAMAGED,
            (
                ("player_index", defending_player_index),
                ("amount", amount),
                ("source", "combat"),
            ),
        )

    def _damage_blocked_exchange(
        self,
        state: GameState,
        *,
        attacker_id: GameObjectId,
        blocker_id: GameObjectId,
        attacker_power: int,
        blocker_power: int,
    ) -> None:
        raw_a = state.get_object(attacker_id)
        raw_b = state.get_object(blocker_id)
        if not isinstance(raw_a, Permanent) or not isinstance(raw_b, Permanent):
            msg = "Échange de combat : attaquant et bloqueur doivent être des permanents."
            raise InvalidGameStateError(msg, field_name="combat")
        if attacker_power > 0:
            raw_b.add_marked_damage(attacker_power)
            state.record_engine_event(
                EventType.COMBAT_DAMAGE_ASSIGNED,
                (
                    ("source_attacker_id", attacker_id.value),
                    ("target_creature_id", blocker_id.value),
                    ("amount", attacker_power),
                ),
            )
        if blocker_power > 0:
            raw_a.add_marked_damage(blocker_power)
            state.record_engine_event(
                EventType.COMBAT_DAMAGE_ASSIGNED,
                (
                    ("source_blocker_id", blocker_id.value),
                    ("target_creature_id", attacker_id.value),
                    ("amount", blocker_power),
                ),
            )

    def _resolve_one_attacker(
        self,
        state: GameState,
        rules: CardGameplayPort,
        *,
        attacker_id: GameObjectId,
        defending_player_index: int,
        blocks_by_attacker: dict[GameObjectId, list[GameObjectId]],
    ) -> None:
        aloc = state.find_location(attacker_id)
        if aloc.zone_type is not ZoneType.BATTLEFIELD:
            msg = "Attaquant absent du champ de bataille."
            raise InvalidGameStateError(msg, field_name="attacker")
        aobj = state.get_object(attacker_id)
        if not isinstance(aobj, Permanent):
            msg = "L'attaquant doit être un permanent."
            raise InvalidGameStateError(msg, field_name="attacker")
        ap = rules.creature_power(aobj.card_reference.catalog_key)
        blockers = blocks_by_attacker.get(attacker_id, ())
        if not blockers:
            if ap > 0:
                self._damage_player_from_unblocked_attacker(
                    state,
                    attacker_id=attacker_id,
                    defending_player_index=defending_player_index,
                    amount=ap,
                )
            return
        blocker_id = blockers[0]
        blobj = state.get_object(blocker_id)
        if not isinstance(blobj, Permanent):
            msg = "Le bloqueur doit être un permanent."
            raise InvalidGameStateError(msg, field_name="blocker")
        bp = rules.creature_power(blobj.card_reference.catalog_key)
        self._damage_blocked_exchange(
            state,
            attacker_id=attacker_id,
            blocker_id=blocker_id,
            attacker_power=ap,
            blocker_power=bp,
        )
