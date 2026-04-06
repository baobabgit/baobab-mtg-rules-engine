"""Validation déterministe de la déclaration de bloqueurs."""

from __future__ import annotations

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.illegal_game_action_error import IllegalGameActionError


class BlockerDeclarationService:
    """Vérifie les contraintes minimales avant :meth:`GameState.apply_declare_blocker`."""

    def validate_and_apply(
        self,
        state: GameState,
        rules: CardGameplayPort,
        *,
        defending_player_index: int,
        blocker_object_id: GameObjectId,
        attacker_object_id: GameObjectId,
    ) -> None:
        """Déclare un bloqueur si l'attaquant est libre et le bloqueur éligible.

        Un seul bloqueur par attaquant est supporté dans ce périmètre.

        :raises IllegalGameActionError: si la déclaration est illégale ou non supportée.
        """
        if attacker_object_id not in state.declared_attackers:
            msg = "L'attaquant doit être déclaré."
            raise IllegalGameActionError(msg, field_name="attacker_object_id")
        for _b, a in state.declared_blocks:
            if a == attacker_object_id:
                msg = "Cet attaquant a déjà un bloqueur dans le périmètre supporté."
                raise IllegalGameActionError(msg, field_name="attacker_object_id")
        bloc_loc = state.find_location(blocker_object_id)
        if (
            bloc_loc.zone_type is not ZoneType.BATTLEFIELD
            or bloc_loc.player_index != defending_player_index
        ):
            msg = "Le bloqueur doit être sur le champ du défenseur."
            raise IllegalGameActionError(msg, field_name="blocker_object_id")
        bobj = state.get_object(blocker_object_id)
        if not isinstance(bobj, Permanent):
            msg = "Seul un permanent peut bloquer."
            raise IllegalGameActionError(msg, field_name="blocker_object_id")
        key = bobj.card_reference.catalog_key
        if not rules.is_creature_catalog_key(key):
            msg = "Seule une créature catalogue peut bloquer."
            raise IllegalGameActionError(msg, field_name="blocker_object_id")
        power = rules.creature_power(key)
        toughness = rules.creature_toughness(key)
        if power < 1 or toughness < 1:
            msg = "Force et endurance catalogue strictement positives requises pour bloquer."
            raise IllegalGameActionError(msg, field_name="blocker_object_id")
        state.apply_declare_blocker(defending_player_index, blocker_object_id, attacker_object_id)
