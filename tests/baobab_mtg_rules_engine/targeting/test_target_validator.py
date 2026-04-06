"""Tests pour :class:`TargetValidator`."""

import pytest

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_spell_target_error import InvalidSpellTargetError
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget
from baobab_mtg_rules_engine.targeting.target_validator import TargetValidator

from ..cast_spell_test_helpers import kill_spell_rules_targeting_creature


def _rules_bolt() -> InMemoryCardCatalogAdapter:
    keys = frozenset({"bolt", "bear"})
    return InMemoryCardCatalogAdapter(
        keys,
        creature_keys=frozenset({"bear"}),
        instant_spell_keys=frozenset({"bolt"}),
        spell_mana_cost_by_key={"bolt": 1},
        spell_target_kind_by_key={"bolt": "player"},
        spell_damage_to_player_by_key={"bolt": 3},
    )


class TestTargetValidator:
    """Nombre et type de cibles."""

    def test_none_requires_empty_targets(self) -> None:
        """Sort sans cible : tuple vide obligatoire."""
        state = GameState.new_two_player()
        rules = InMemoryCardCatalogAdapter(
            frozenset({"x"}),
            sorcery_spell_keys=frozenset({"x"}),
            spell_mana_cost_by_key={"x": 0},
        )
        v = TargetValidator()
        v.validate_at_cast(
            state,
            rules,
            caster_player_index=0,
            spell_catalog_key="x",
            targets=(),
        )
        with pytest.raises(InvalidSpellTargetError, match="pas de cible"):
            v.validate_at_cast(
                state,
                rules,
                caster_player_index=0,
                spell_catalog_key="x",
                targets=(SimpleTarget.for_player(0),),
            )

    def test_player_target_valid_at_cast(self) -> None:
        """Cible joueur acceptée pour un sort ``player``."""
        state = GameState.new_two_player()
        rules = _rules_bolt()
        TargetValidator().validate_at_cast(
            state,
            rules,
            caster_player_index=0,
            spell_catalog_key="bolt",
            targets=(SimpleTarget.for_player(1),),
        )

    def test_permanent_that_is_not_creature_catalog_rejected(self) -> None:
        """Un permanent dont la clé n'est pas créature dans le catalogue est refusé."""
        state = GameState.new_two_player()
        oid = state.issue_object_id()
        state.register_object_at(
            Permanent(oid, CardReference("bear")),
            ZoneLocation(0, ZoneType.BATTLEFIELD),
        )
        rules = InMemoryCardCatalogAdapter(
            frozenset({"kill", "bear"}),
            sorcery_spell_keys=frozenset({"kill"}),
            spell_mana_cost_by_key={"kill": 1},
            spell_target_kind_by_key={"kill": "creature"},
        )
        with pytest.raises(InvalidSpellTargetError, match="créature"):
            TargetValidator().validate_at_cast(
                state,
                rules,
                caster_player_index=0,
                spell_catalog_key="kill",
                targets=(SimpleTarget.for_permanent(oid),),
            )

    def test_creature_target_must_be_on_battlefield(self) -> None:
        """Créature inexistante refusée."""
        state = GameState.new_two_player()
        rules = InMemoryCardCatalogAdapter(
            frozenset({"kill"}),
            sorcery_spell_keys=frozenset({"kill"}),
            creature_keys=frozenset({"bear"}),
            spell_mana_cost_by_key={"kill": 1},
            spell_target_kind_by_key={"kill": "creature"},
        )
        with pytest.raises(InvalidSpellTargetError, match="créature"):
            TargetValidator().validate_at_cast(
                state,
                rules,
                caster_player_index=0,
                spell_catalog_key="kill",
                targets=(SimpleTarget.for_permanent(GameObjectId(99)),),
            )

    def test_resolution_false_if_creature_left_battlefield(self) -> None:
        """La cible créature doit encore être au champ à la résolution."""
        state = GameState.new_two_player()
        rules = kill_spell_rules_targeting_creature()
        cid = state.issue_object_id()
        state.register_object_at(
            Permanent(cid, CardReference("bear")),
            ZoneLocation(1, ZoneType.BATTLEFIELD),
        )
        v = TargetValidator()
        targets = (SimpleTarget.for_permanent(cid),)
        assert v.all_targets_still_legal_at_resolution(
            state,
            rules,
            spell_catalog_key="kill",
            targets=targets,
        )
        grave = ZoneLocation(1, ZoneType.GRAVEYARD)
        state.relocate_preserving_identity(cid, grave)
        assert not v.all_targets_still_legal_at_resolution(
            state,
            rules,
            spell_catalog_key="kill",
            targets=targets,
        )
