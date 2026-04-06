"""Représentation sérialisable d'une action de jeu pour replay et non-régression."""

from __future__ import annotations

from dataclasses import dataclass

from baobab_mtg_rules_engine.actions.activate_simple_ability_action import (
    ActivateSimpleAbilityAction,
)
from baobab_mtg_rules_engine.actions.cast_spell_action import CastSpellAction
from baobab_mtg_rules_engine.actions.declare_attacker_action import DeclareAttackerAction
from baobab_mtg_rules_engine.actions.declare_blocker_action import DeclareBlockerAction
from baobab_mtg_rules_engine.actions.game_action import GameAction
from baobab_mtg_rules_engine.actions.pass_priority_action import PassPriorityAction
from baobab_mtg_rules_engine.actions.play_land_action import PlayLandAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.exceptions.replay_sequence_error import ReplaySequenceError
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget


@dataclass(frozen=True, slots=True)
class RecordedGameAction:
    """Action enregistrée sous forme stable (nom de famille + paramètres sérialisés).

    Les références d'objets passent par des **alias** logiques résolus au replay
    (champ ``object_aliases`` du contexte de scénario).

    :param kind: Nom de :class:`SupportedActionKind` (ex. ``\"PASS_PRIORITY\"``).
    :param parameters: Paires ``(clé, valeur)`` ; les alias utilisent la clé ``object_alias``,
        ``spell_alias``, ``permanent_alias``, ``attacker_alias``, ``blocker_alias`` selon le cas.
    """

    kind: str
    parameters: tuple[tuple[str, str | int], ...] = ()

    @staticmethod
    def pass_priority() -> RecordedGameAction:
        """:return: Passe de priorité enregistrée."""
        return RecordedGameAction(SupportedActionKind.PASS_PRIORITY.name, ())

    @staticmethod
    def play_land(*, object_alias: str) -> RecordedGameAction:
        """:return: Jouer un terrain depuis la main (alias de la carte en main)."""
        return RecordedGameAction(
            SupportedActionKind.PLAY_LAND.name,
            (("object_alias", object_alias),),
        )

    @staticmethod
    def cast_spell(
        *, spell_alias: str, target_parameters: tuple[tuple[str, str | int], ...]
    ) -> RecordedGameAction:
        """:return: Lancer un sort ; cibles via ``target_parameters`` (cf. replay)."""
        params: list[tuple[str, str | int]] = [("spell_alias", spell_alias)]
        params.extend(target_parameters)
        return RecordedGameAction(SupportedActionKind.CAST_SPELL.name, tuple(params))

    @staticmethod
    def activate_simple_ability(
        *, permanent_alias: str, generic_mana_cost: int
    ) -> RecordedGameAction:
        """:return: Activation d'une capacité simple (coût générique entier)."""
        return RecordedGameAction(
            SupportedActionKind.ACTIVATE_SIMPLE_ABILITY.name,
            (
                ("permanent_alias", permanent_alias),
                ("generic_mana_cost", generic_mana_cost),
            ),
        )

    @staticmethod
    def declare_attacker(*, creature_alias: str) -> RecordedGameAction:
        """:return: Déclaration d'attaquant."""
        return RecordedGameAction(
            SupportedActionKind.DECLARE_ATTACKER.name,
            (("creature_alias", creature_alias),),
        )

    @staticmethod
    def declare_blocker(*, blocker_alias: str, attacker_alias: str) -> RecordedGameAction:
        """:return: Déclaration de bloqueur."""
        return RecordedGameAction(
            SupportedActionKind.DECLARE_BLOCKER.name,
            (
                ("blocker_alias", blocker_alias),
                ("attacker_alias", attacker_alias),
            ),
        )

    @staticmethod
    def from_game_action(action: GameAction, *, id_to_alias: dict[int, str]) -> RecordedGameAction:
        """Enregistre une :class:`GameAction` avec une table id→alias.

        :raises ReplaySequenceError: alias manquant ou type d'action non supporté.
        """
        if isinstance(action, PassPriorityAction):
            return RecordedGameAction.pass_priority()
        if isinstance(action, PlayLandAction):
            alias = id_to_alias.get(action.land_object_id.value)
            if alias is None:
                msg = "Alias manquant pour le terrain joué."
                raise ReplaySequenceError(msg, field_name="land_object_id")
            return RecordedGameAction.play_land(object_alias=alias)
        if isinstance(action, CastSpellAction):
            salias = id_to_alias.get(action.spell_object_id.value)
            if salias is None:
                msg = "Alias manquant pour le sort lancé."
                raise ReplaySequenceError(msg, field_name="spell_object_id")
            target_params = _encode_targets(action.targets, id_to_alias=id_to_alias)
            return RecordedGameAction.cast_spell(
                spell_alias=salias, target_parameters=target_params
            )
        if isinstance(action, ActivateSimpleAbilityAction):
            palias = id_to_alias.get(action.permanent_object_id.value)
            if palias is None:
                msg = "Alias manquant pour le permanent activé."
                raise ReplaySequenceError(msg, field_name="permanent_object_id")
            return RecordedGameAction.activate_simple_ability(
                permanent_alias=palias,
                generic_mana_cost=action.generic_mana_cost,
            )
        if isinstance(action, DeclareAttackerAction):
            alias = id_to_alias.get(action.creature_object_id.value)
            if alias is None:
                msg = "Alias manquant pour l'attaquant."
                raise ReplaySequenceError(msg, field_name="creature_object_id")
            return RecordedGameAction.declare_attacker(creature_alias=alias)
        if isinstance(action, DeclareBlockerAction):
            b_alias = id_to_alias.get(action.blocker_object_id.value)
            a_alias = id_to_alias.get(action.attacker_object_id.value)
            if b_alias is None or a_alias is None:
                msg = "Alias manquant pour bloqueur ou attaquant."
                raise ReplaySequenceError(msg, field_name="blocker_object_id")
            return RecordedGameAction.declare_blocker(blocker_alias=b_alias, attacker_alias=a_alias)
        msg = f"Type d'action non enregistrable pour replay : {type(action)!r}."
        raise ReplaySequenceError(msg, field_name="action")


def _encode_targets(
    targets: tuple[SimpleTarget, ...],
    *,
    id_to_alias: dict[int, str],
) -> tuple[tuple[str, str | int], ...]:
    if len(targets) == 0:
        return (("target_mode", "none"),)
    if len(targets) != 1:
        msg = "Seules les cibles simples 0/1 sont supportées pour l'enregistrement."
        raise ReplaySequenceError(msg, field_name="targets")
    t = targets[0]
    if t.player_index is not None:
        return (("target_mode", "player"), ("player_index", t.player_index))
    perm = t.permanent_object_id
    if perm is None:
        msg = "Cible permanent incohérente."
        raise ReplaySequenceError(msg, field_name="targets")
    palias = id_to_alias.get(perm.value)
    if palias is None:
        msg = "Alias manquant pour la cible créature."
        raise ReplaySequenceError(msg, field_name="targets")
    return (("target_mode", "permanent"), ("permanent_alias", palias))


def _cast_spell_targets_from_replay_params(
    params: dict[str, str | int],
    *,
    object_aliases: dict[str, GameObjectId],
) -> tuple[SimpleTarget, ...]:
    """Construit le tuple de cibles pour un CAST_SPELL rejoué."""
    mode = params.get("target_mode")
    if mode == "none":
        return ()
    if mode == "player":
        idx = params.get("player_index")
        if not isinstance(idx, int) or idx not in (0, 1):
            msg = "Index joueur invalide pour la cible de sort."
            raise ReplaySequenceError(msg, field_name="player_index")
        return (SimpleTarget.for_player(idx),)
    if mode == "permanent":
        perm_alias = params.get("permanent_alias")
        if not isinstance(perm_alias, str):
            msg = "Alias de permanent cible manquant."
            raise ReplaySequenceError(msg, field_name="permanent_alias")
        perm_id = object_aliases.get(perm_alias)
        if perm_id is None:
            msg = f"Alias permanent inconnu : {perm_alias!r}."
            raise ReplaySequenceError(msg, field_name="permanent_alias")
        return (SimpleTarget.for_permanent(perm_id),)
    msg = "target_mode de sort manquant ou non supporté pour le replay."
    raise ReplaySequenceError(msg, field_name="target_mode")


def resolve_to_game_action(
    recorded: RecordedGameAction,
    *,
    object_aliases: dict[str, GameObjectId],
) -> GameAction:
    """Convertit un enregistrement en :class:`GameAction` via les alias d'objets.

    :raises ReplaySequenceError: si le genre d'action ou les paramètres sont invalides.
    """
    try:
        sk = SupportedActionKind[recorded.kind]
    except KeyError as exc:
        msg = f"Genre d'action de replay inconnu : {recorded.kind!r}."
        raise ReplaySequenceError(msg, field_name="kind") from exc
    params = dict(recorded.parameters)

    def _alias_oid(key: str) -> GameObjectId:
        name = params.get(key)
        if not isinstance(name, str):
            msg = f"Paramètre alias manquant ou invalide : {key!r}."
            raise ReplaySequenceError(msg, field_name=key)
        oid = object_aliases.get(name)
        if oid is None:
            msg = f"Alias d'objet inconnu : {name!r}."
            raise ReplaySequenceError(msg, field_name=key)
        return oid

    if sk is SupportedActionKind.PASS_PRIORITY:
        if recorded.parameters:
            msg = "PASS_PRIORITY ne doit pas avoir de paramètres."
            raise ReplaySequenceError(msg, field_name="parameters")
        return PassPriorityAction()
    if sk is SupportedActionKind.PLAY_LAND:
        return PlayLandAction(_alias_oid("object_alias"))
    if sk is SupportedActionKind.CAST_SPELL:
        spell_id = _alias_oid("spell_alias")
        targets = _cast_spell_targets_from_replay_params(params, object_aliases=object_aliases)
        return CastSpellAction(spell_id, targets)
    if sk is SupportedActionKind.ACTIVATE_SIMPLE_ABILITY:
        cost = params.get("generic_mana_cost")
        if not isinstance(cost, int):
            msg = "Coût générique entier requis pour l'activation."
            raise ReplaySequenceError(msg, field_name="generic_mana_cost")
        return ActivateSimpleAbilityAction(_alias_oid("permanent_alias"), cost)
    if sk is SupportedActionKind.DECLARE_ATTACKER:
        return DeclareAttackerAction(_alias_oid("creature_alias"))
    if sk is SupportedActionKind.DECLARE_BLOCKER:
        return DeclareBlockerAction(
            _alias_oid("blocker_alias"),
            _alias_oid("attacker_alias"),
        )
    msg = f"Genre d'action supporté mais non routé : {sk.name}."
    raise ReplaySequenceError(msg, field_name="kind")
