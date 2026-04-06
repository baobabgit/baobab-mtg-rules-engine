"""Tests pour :class:`RecordedGameAction` et résolution."""

import pytest

from baobab_mtg_rules_engine.actions.cast_spell_action import CastSpellAction
from baobab_mtg_rules_engine.actions.declare_attacker_action import DeclareAttackerAction
from baobab_mtg_rules_engine.actions.declare_blocker_action import DeclareBlockerAction
from baobab_mtg_rules_engine.actions.activate_simple_ability_action import (
    ActivateSimpleAbilityAction,
)
from baobab_mtg_rules_engine.actions.game_action import GameAction
from baobab_mtg_rules_engine.actions.pass_priority_action import PassPriorityAction
from baobab_mtg_rules_engine.actions.play_land_action import PlayLandAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.exceptions.replay_sequence_error import ReplaySequenceError
from baobab_mtg_rules_engine.replay.recorded_game_action import (
    RecordedGameAction,
    resolve_to_game_action,
)
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget


class TestRecordedGameAction:
    """Round-trip alias ↔ action."""

    def test_resolve_pass_priority(self) -> None:
        """Passe : aucun alias requis."""
        act = resolve_to_game_action(
            RecordedGameAction.pass_priority(),
            object_aliases={},
        )
        assert isinstance(act, PassPriorityAction)

    def test_resolve_play_land(self) -> None:
        """Terrain : résolution par alias."""
        oid = GameObjectId(5)
        act = resolve_to_game_action(
            RecordedGameAction.play_land(object_alias="f1"),
            object_aliases={"f1": oid},
        )
        assert isinstance(act, PlayLandAction)
        assert act.land_object_id == oid

    def test_unknown_kind_raises(self) -> None:
        """Genre inconnu : erreur explicite."""
        with pytest.raises(ReplaySequenceError, match="inconnu"):
            resolve_to_game_action(
                RecordedGameAction("NOT_A_KIND", ()),
                object_aliases={},
            )

    def test_from_game_action_roundtrip(self) -> None:
        """Enregistrement puis résolution retrouve l'équivalence."""
        oid = GameObjectId(9)
        original = PlayLandAction(oid)
        rec = RecordedGameAction.from_game_action(original, id_to_alias={oid.value: "land_a"})
        resolved = resolve_to_game_action(rec, object_aliases={"land_a": oid})
        assert resolved == original

    def test_resolve_cast_spell_no_target(self) -> None:
        """Sort sans cible."""
        sid = GameObjectId(2)
        act = resolve_to_game_action(
            RecordedGameAction.cast_spell(
                spell_alias="s1",
                target_parameters=(("target_mode", "none"),),
            ),
            object_aliases={"s1": sid},
        )
        assert isinstance(act, CastSpellAction)
        assert act.spell_object_id == sid
        assert act.targets == ()

    def test_resolve_cast_spell_player_target(self) -> None:
        """Sort ciblant un joueur."""
        sid = GameObjectId(3)
        act = resolve_to_game_action(
            RecordedGameAction.cast_spell(
                spell_alias="bolt",
                target_parameters=(("target_mode", "player"), ("player_index", 1)),
            ),
            object_aliases={"bolt": sid},
        )
        assert isinstance(act, CastSpellAction)
        assert act.targets == (SimpleTarget.for_player(1),)

    def test_resolve_cast_spell_permanent_target(self) -> None:
        """Sort ciblant un permanent par alias."""
        sid = GameObjectId(4)
        bear = GameObjectId(5)
        act = resolve_to_game_action(
            RecordedGameAction.cast_spell(
                spell_alias="kill",
                target_parameters=(("target_mode", "permanent"), ("permanent_alias", "bear1")),
            ),
            object_aliases={"kill": sid, "bear1": bear},
        )
        assert isinstance(act, CastSpellAction)
        assert act.targets == (SimpleTarget.for_permanent(bear),)

    def test_resolve_activate_and_declare(self) -> None:
        """Activation et déclarations de combat."""
        perm = GameObjectId(10)
        atk = GameObjectId(11)
        blk = GameObjectId(12)
        aa = resolve_to_game_action(
            RecordedGameAction.activate_simple_ability(permanent_alias="p", generic_mana_cost=2),
            object_aliases={"p": perm},
        )
        assert isinstance(aa, ActivateSimpleAbilityAction)
        assert aa.permanent_object_id == perm
        da = resolve_to_game_action(
            RecordedGameAction.declare_attacker(creature_alias="a"),
            object_aliases={"a": atk},
        )
        assert isinstance(da, DeclareAttackerAction)
        assert da.creature_object_id == atk
        db = resolve_to_game_action(
            RecordedGameAction.declare_blocker(blocker_alias="b", attacker_alias="a"),
            object_aliases={"b": blk, "a": atk},
        )
        assert isinstance(db, DeclareBlockerAction)
        assert db.blocker_object_id == blk
        assert db.attacker_object_id == atk

    def test_from_game_action_cast_roundtrip(self) -> None:
        """Sort avec cible joueur : round-trip."""
        sid = GameObjectId(20)
        orig = CastSpellAction(sid, (SimpleTarget.for_player(0),))
        rec = RecordedGameAction.from_game_action(orig, id_to_alias={sid.value: "spell_x"})
        resolved = resolve_to_game_action(rec, object_aliases={"spell_x": sid})
        assert resolved == orig

    def test_from_game_action_missing_alias_raises(self) -> None:
        """Sans alias, enregistrement refusé."""
        with pytest.raises(ReplaySequenceError, match="Alias manquant"):
            RecordedGameAction.from_game_action(PlayLandAction(GameObjectId(1)), id_to_alias={})

    def test_pass_with_parameters_raises(self) -> None:
        """PASS_PRIORITY avec paramètres : rejet."""
        with pytest.raises(ReplaySequenceError, match="PASS_PRIORITY"):
            resolve_to_game_action(
                RecordedGameAction("PASS_PRIORITY", (("x", 1),)),
                object_aliases={},
            )

    def test_resolve_unknown_target_mode_raises(self) -> None:
        """Cible de sort invalide."""
        with pytest.raises(ReplaySequenceError, match="target_mode"):
            resolve_to_game_action(
                RecordedGameAction(
                    "CAST_SPELL",
                    (
                        ("spell_alias", "s"),
                        ("target_mode", "invalid"),
                    ),
                ),
                object_aliases={"s": GameObjectId(1)},
            )

    def test_from_game_action_declare_roundtrip(self) -> None:
        """Déclarations enregistrées puis rejouées."""
        atk = GameObjectId(30)
        blk = GameObjectId(31)
        orig_a = DeclareAttackerAction(atk)
        rec_a = RecordedGameAction.from_game_action(orig_a, id_to_alias={atk.value: "atk1"})
        assert resolve_to_game_action(rec_a, object_aliases={"atk1": atk}) == orig_a
        orig_b = DeclareBlockerAction(blk, atk)
        rec_b = RecordedGameAction.from_game_action(
            orig_b,
            id_to_alias={blk.value: "blk1", atk.value: "atk1"},
        )
        assert resolve_to_game_action(rec_b, object_aliases={"blk1": blk, "atk1": atk}) == orig_b

    def test_from_game_action_cast_creature_roundtrip(self) -> None:
        """Sort ciblant créature : round-trip."""
        sid = GameObjectId(40)
        bear = GameObjectId(41)
        orig = CastSpellAction(sid, (SimpleTarget.for_permanent(bear),))
        rec = RecordedGameAction.from_game_action(
            orig,
            id_to_alias={sid.value: "kill", bear.value: "bear"},
        )
        resolved = resolve_to_game_action(rec, object_aliases={"kill": sid, "bear": bear})
        assert resolved == orig

    def test_from_game_action_pass_priority_roundtrip(self) -> None:
        """La passe d'enregistrement ne porte pas de paramètres."""
        orig = PassPriorityAction()
        rec = RecordedGameAction.from_game_action(orig, id_to_alias={})
        assert rec == RecordedGameAction.pass_priority()
        assert resolve_to_game_action(rec, object_aliases={}) == orig

    def test_from_game_action_activate_simple_ability_roundtrip(self) -> None:
        """Activation enregistrée avec coût générique."""
        perm = GameObjectId(61)
        orig = ActivateSimpleAbilityAction(perm, 3)
        rec = RecordedGameAction.from_game_action(orig, id_to_alias={perm.value: "p1"})
        resolved = resolve_to_game_action(rec, object_aliases={"p1": perm})
        assert resolved == orig

    def test_from_game_action_unsupported_type_raises(self) -> None:
        """Action hors périmètre d'enregistrement : erreur explicite."""

        class _OtherAction(GameAction):
            @property
            def kind(self) -> SupportedActionKind:
                return SupportedActionKind.PASS_PRIORITY

            def sort_key(self) -> tuple[object, ...]:
                return ()

        with pytest.raises(ReplaySequenceError, match="non enregistrable"):
            RecordedGameAction.from_game_action(_OtherAction(), id_to_alias={})

    def test_from_game_action_cast_spell_missing_spell_alias_raises(self) -> None:
        """Sort sans entrée id→alias pour l'objet sort."""
        sid = GameObjectId(50)
        orig = CastSpellAction(sid, ())
        with pytest.raises(ReplaySequenceError, match="sort"):
            RecordedGameAction.from_game_action(orig, id_to_alias={})

    def test_from_game_action_cast_target_missing_permanent_alias_raises(self) -> None:
        """Cible permanent sans alias dans la table."""
        sid = GameObjectId(51)
        bear = GameObjectId(52)
        orig = CastSpellAction(sid, (SimpleTarget.for_permanent(bear),))
        with pytest.raises(ReplaySequenceError, match="cible"):
            RecordedGameAction.from_game_action(orig, id_to_alias={sid.value: "s"})

    def test_from_game_action_multi_target_raises(self) -> None:
        """Plus d'une cible : refus à l'enregistrement."""
        sid = GameObjectId(53)
        orig = CastSpellAction(
            sid,
            (SimpleTarget.for_player(0), SimpleTarget.for_player(1)),
        )
        with pytest.raises(ReplaySequenceError, match="0/1"):
            RecordedGameAction.from_game_action(orig, id_to_alias={sid.value: "s"})

    def test_from_game_action_activate_missing_alias_raises(self) -> None:
        """Activation sans alias permanent."""
        perm = GameObjectId(60)
        with pytest.raises(ReplaySequenceError, match="permanent"):
            RecordedGameAction.from_game_action(
                ActivateSimpleAbilityAction(perm, 1),
                id_to_alias={},
            )

    def test_from_game_action_declare_attacker_missing_alias_raises(self) -> None:
        """Attaquant sans alias."""
        with pytest.raises(ReplaySequenceError, match="attaquant"):
            RecordedGameAction.from_game_action(
                DeclareAttackerAction(GameObjectId(70)),
                id_to_alias={},
            )

    def test_from_game_action_declare_blocker_missing_alias_raises(self) -> None:
        """Bloqueur sans alias."""
        with pytest.raises(ReplaySequenceError, match="bloqueur"):
            RecordedGameAction.from_game_action(
                DeclareBlockerAction(GameObjectId(71), GameObjectId(72)),
                id_to_alias={71: "b"},
            )

    def test_resolve_cast_spell_invalid_player_index_raises(self) -> None:
        """Index joueur hors 0/1."""
        with pytest.raises(ReplaySequenceError, match="Index joueur"):
            resolve_to_game_action(
                RecordedGameAction(
                    "CAST_SPELL",
                    (
                        ("spell_alias", "s"),
                        ("target_mode", "player"),
                        ("player_index", 5),
                    ),
                ),
                object_aliases={"s": GameObjectId(1)},
            )

    def test_resolve_cast_spell_permanent_alias_not_string_raises(self) -> None:
        """permanent_alias absent ou non chaîne."""
        with pytest.raises(ReplaySequenceError, match="permanent cible"):
            resolve_to_game_action(
                RecordedGameAction(
                    "CAST_SPELL",
                    (
                        ("spell_alias", "s"),
                        ("target_mode", "permanent"),
                    ),
                ),
                object_aliases={"s": GameObjectId(1)},
            )

    def test_resolve_cast_spell_unknown_permanent_alias_raises(self) -> None:
        """Alias de permanent inconnu au replay."""
        with pytest.raises(ReplaySequenceError, match="permanent inconnu"):
            resolve_to_game_action(
                RecordedGameAction(
                    "CAST_SPELL",
                    (
                        ("spell_alias", "s"),
                        ("target_mode", "permanent"),
                        ("permanent_alias", "ghost"),
                    ),
                ),
                object_aliases={"s": GameObjectId(1)},
            )

    def test_resolve_activate_invalid_cost_raises(self) -> None:
        """Coût générique manquant ou non entier."""
        with pytest.raises(ReplaySequenceError, match="Coût générique"):
            resolve_to_game_action(
                RecordedGameAction(
                    "ACTIVATE_SIMPLE_ABILITY",
                    (("permanent_alias", "p"), ("generic_mana_cost", "x")),
                ),
                object_aliases={"p": GameObjectId(1)},
            )

    def test_resolve_missing_object_alias_key_raises(self) -> None:
        """Clé d'alias manquante dans les paramètres."""
        with pytest.raises(ReplaySequenceError, match="object_alias"):
            resolve_to_game_action(
                RecordedGameAction("PLAY_LAND", ()),
                object_aliases={"f1": GameObjectId(1)},
            )

    def test_resolve_unknown_object_alias_raises(self) -> None:
        """Alias référencé mais absent du dictionnaire."""
        with pytest.raises(ReplaySequenceError, match="inconnu"):
            resolve_to_game_action(
                RecordedGameAction.play_land(object_alias="missing"),
                object_aliases={},
            )
