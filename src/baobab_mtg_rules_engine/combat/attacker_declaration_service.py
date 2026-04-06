"""Validation déterministe de la déclaration d'attaquants."""

from __future__ import annotations

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.illegal_game_action_error import IllegalGameActionError


class AttackerDeclarationService:
    """Vérifie les contraintes minimales avant :meth:`GameState.apply_declare_attacker`."""

    def validate_and_apply(
        self,
        state: GameState,
        rules: CardGameplayPort,
        *,
        active_player_index: int,
        creature_object_id: GameObjectId,
    ) -> None:
        """Déclare un attaquant si la créature est éligible (type, force/endurance catalogue).

        :raises IllegalGameActionError: si la déclaration est hors périmètre supporté.
        """
        loc = state.find_location(creature_object_id)
        if loc.zone_type is not ZoneType.BATTLEFIELD or loc.player_index != active_player_index:
            msg = "L'attaquant doit être sur le champ du joueur actif."
            raise IllegalGameActionError(msg, field_name="creature_object_id")
        obj = state.get_object(creature_object_id)
        if not isinstance(obj, Permanent):
            msg = "Seul un permanent peut attaquer."
            raise IllegalGameActionError(msg, field_name="creature_object_id")
        key = obj.card_reference.catalog_key
        if not rules.is_creature_catalog_key(key):
            msg = "Seule une créature catalogue peut être déclarée attaquante."
            raise IllegalGameActionError(msg, field_name="creature_object_id")
        power = rules.creature_power(key)
        toughness = rules.creature_toughness(key)
        if power < 1 or toughness < 1:
            msg = "Force et endurance catalogue strictement positives requises pour attaquer."
            raise IllegalGameActionError(msg, field_name="creature_object_id")
        state.apply_declare_attacker(active_player_index, creature_object_id)
