"""Validation des cibles au lancement et à la résolution."""

from __future__ import annotations

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError
from baobab_mtg_rules_engine.exceptions.invalid_spell_target_error import InvalidSpellTargetError
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget


class TargetValidator:
    """Contrôle le nombre et le type de cibles selon le port gameplay."""

    def validate_at_cast(
        self,
        state: GameState,
        rules: CardGameplayPort,
        *,
        caster_player_index: int,
        spell_catalog_key: str,
        targets: tuple[SimpleTarget, ...],
    ) -> None:
        """Vérifie les cibles avant paiement et mise sur la pile.

        :raises InvalidSpellTargetError: si le nombre ou le type de cibles est incohérent.
        """
        _ = caster_player_index
        kind = rules.spell_target_kind(spell_catalog_key)
        self._expect_target_count(kind, targets)
        if kind == "none":
            return
        target = targets[0]
        if kind == "player":
            if target.player_index is None:
                msg = "Ce sort exige une cible joueur."
                raise InvalidSpellTargetError(msg, field_name="targets")
            return
        if kind == "creature":
            if target.permanent_object_id is None:
                msg = "Ce sort exige une cible créature (permanent)."
                raise InvalidSpellTargetError(msg, field_name="targets")
            self._assert_valid_creature_target(state, rules, target.permanent_object_id)
            return
        msg = f"Kind de cible catalogue non supporté : {kind!r}."
        raise InvalidSpellTargetError(msg, field_name="spell_catalog_key")

    def all_targets_still_legal_at_resolution(
        self,
        state: GameState,
        rules: CardGameplayPort,
        *,
        spell_catalog_key: str,
        targets: tuple[SimpleTarget, ...],
    ) -> bool:
        """:return: ``False`` si au moins une cible requise est devenue illégale."""
        kind = rules.spell_target_kind(spell_catalog_key)
        if kind == "none":
            return True
        if len(targets) != 1:
            return False
        target = targets[0]
        if kind == "player":
            return target.player_index is not None and target.player_index in (0, 1)
        if kind == "creature":
            if target.permanent_object_id is None:
                return False
            return self._is_valid_creature_target(state, rules, target.permanent_object_id)
        return False

    def _expect_target_count(self, kind: str, targets: tuple[SimpleTarget, ...]) -> None:
        if kind == "none":
            if len(targets) != 0:
                msg = "Ce sort ne prend pas de cible."
                raise InvalidSpellTargetError(msg, field_name="targets")
            return
        if len(targets) != 1:
            msg = "Ce sort exige exactement une cible."
            raise InvalidSpellTargetError(msg, field_name="targets")

    def _assert_valid_creature_target(
        self,
        state: GameState,
        rules: CardGameplayPort,
        object_id: GameObjectId,
    ) -> None:
        if not self._is_valid_creature_target(state, rules, object_id):
            msg = "La créature ciblée doit être un permanent créature sur le champ de bataille."
            raise InvalidSpellTargetError(msg, field_name="targets")

    def _is_valid_creature_target(
        self,
        state: GameState,
        rules: CardGameplayPort,
        object_id: GameObjectId,
    ) -> bool:
        try:
            loc = state.find_location(object_id)
        except InvalidGameStateError:
            return False
        if loc.zone_type is not ZoneType.BATTLEFIELD:
            return False
        obj = state.get_object(object_id)
        if not isinstance(obj, Permanent):
            return False
        return rules.is_creature_catalog_key(obj.card_reference.catalog_key)
