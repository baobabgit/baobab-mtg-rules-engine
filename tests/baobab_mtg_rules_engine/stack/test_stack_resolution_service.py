"""Tests pour :class:`StackResolutionService`."""

import pytest

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError
from baobab_mtg_rules_engine.stack.stack_resolution_service import StackResolutionService
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget

from ..cast_spell_test_helpers import cast_spell_from_hand, kill_spell_rules_targeting_creature


def _golem_rules() -> InMemoryCardCatalogAdapter:
    return InMemoryCardCatalogAdapter(
        frozenset({"golem"}),
        sorcery_spell_keys=frozenset({"golem"}),
        creature_spell_keys=frozenset({"golem"}),
        spell_mana_cost_by_key={"golem": 1},
    )


class TestStackResolutionService:
    """Ordre LIFO et effets simples."""

    def test_empty_stack_raises(self) -> None:
        """Résolution impossible sans objet sur la pile."""
        state = GameState.new_two_player()
        rules = _golem_rules()
        with pytest.raises(InvalidGameStateError, match="vide"):
            StackResolutionService().resolve_top(state, rules)

    def test_creature_spell_becomes_permanent(self) -> None:
        """Sommet résolu : créature sur le champ du contrôleur."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        hid = state.issue_object_id()
        state.register_object_at(
            InGameCard(hid, CardReference("golem")),
            ZoneLocation(0, ZoneType.HAND),
        )
        state.players[0].add_floating_mana(2)
        rules = _golem_rules()
        cast_spell_from_hand(
            state,
            rules,
            caster_player_index=0,
            spell_hand_object_id=hid,
            targets=(),
        )
        StackResolutionService().resolve_top(state, rules)
        assert len(state.stack_zone.object_ids()) == 0
        bf = state.players[0].zone(ZoneType.BATTLEFIELD).object_ids()
        assert len(bf) == 1
        obj = state.get_object(bf[0])
        assert isinstance(obj, Permanent)
        assert EventType.SPELL_RESOLVED in [e.event_type for e in state.events]

    def test_fizzle_when_creature_target_illegal(self) -> None:
        """Cible créature partie du champ : fizzle vers défausse."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        bear = state.issue_object_id()
        state.register_object_at(
            Permanent(bear, CardReference("bear")),
            ZoneLocation(1, ZoneType.BATTLEFIELD),
        )
        kill_hand = state.issue_object_id()
        state.register_object_at(
            InGameCard(kill_hand, CardReference("kill")),
            ZoneLocation(0, ZoneType.HAND),
        )
        state.players[0].add_floating_mana(2)
        rules = kill_spell_rules_targeting_creature()
        cast_spell_from_hand(
            state,
            rules,
            caster_player_index=0,
            spell_hand_object_id=kill_hand,
            targets=(SimpleTarget.for_permanent(bear),),
        )
        state.relocate_preserving_identity(bear, ZoneLocation(1, ZoneType.GRAVEYARD))
        StackResolutionService().resolve_top(state, rules)
        assert EventType.SPELL_FIZZLED in [e.event_type for e in state.events]
        assert len(state.stack_zone.object_ids()) == 0

    def test_damage_spell_applies_to_player(self) -> None:
        """Sort dégâts joueur : PV puis défausse."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        hid = state.issue_object_id()
        state.register_object_at(
            InGameCard(hid, CardReference("bolt")),
            ZoneLocation(0, ZoneType.HAND),
        )
        state.players[0].add_floating_mana(2)
        rules = InMemoryCardCatalogAdapter(
            frozenset({"bolt"}),
            sorcery_spell_keys=frozenset({"bolt"}),
            spell_mana_cost_by_key={"bolt": 1},
            spell_target_kind_by_key={"bolt": "player"},
            spell_damage_to_player_by_key={"bolt": 4},
        )
        cast_spell_from_hand(
            state,
            rules,
            caster_player_index=0,
            spell_hand_object_id=hid,
            targets=(SimpleTarget.for_player(1),),
        )
        life_before = state.players[1].life_total
        StackResolutionService().resolve_top(state, rules)
        assert state.players[1].life_total == life_before - 4
        assert EventType.PLAYER_DAMAGED in [e.event_type for e in state.events]
