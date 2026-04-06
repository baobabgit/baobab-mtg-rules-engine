"""Tests pour :class:`SpellCastService`."""

import pytest

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.spell_on_stack import SpellOnStack
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.illegal_game_action_error import IllegalGameActionError
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget

from ..cast_spell_test_helpers import cast_spell_from_hand


def _catalog_golem() -> InMemoryCardCatalogAdapter:
    keys = frozenset({"golem"})
    return InMemoryCardCatalogAdapter(
        keys,
        sorcery_spell_keys=frozenset({"golem"}),
        creature_spell_keys=frozenset({"golem"}),
        spell_mana_cost_by_key={"golem": 2},
    )


class TestSpellCastServiceCreature:
    """Sort créature."""

    def test_creature_spell_resolves_timing_and_puts_stack_metadata(self) -> None:
        """Rituel + créature : main vide, pile avec vue :class:`StackObject`."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        hand_id = state.issue_object_id()
        state.register_object_at(
            InGameCard(hand_id, CardReference("golem")),
            ZoneLocation(0, ZoneType.HAND),
        )
        state.players[0].add_floating_mana(3)
        rules = _catalog_golem()
        stack_id = cast_spell_from_hand(
            state,
            rules,
            caster_player_index=0,
            spell_hand_object_id=hand_id,
            targets=(),
        )
        assert len(state.stack_zone.object_ids()) == 1
        view = state.get_stack_object_view(stack_id)
        assert view is not None
        assert view.catalog_key == "golem"
        assert view.controller_player_index == 0


class TestSpellCastServiceUnclassified:
    """Refus explicite si le catalogue ne classe pas le sort."""

    def test_spell_without_speed_flags_raises(self) -> None:
        """Clé connue comme sort en main mais sans rituel/éphémère/créature refusée."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        hid = state.issue_object_id()
        state.register_object_at(
            InGameCard(hid, CardReference("orphan")),
            ZoneLocation(0, ZoneType.HAND),
        )
        state.players[0].add_floating_mana(2)
        rules = InMemoryCardCatalogAdapter(
            frozenset({"orphan"}),
            spell_mana_cost_by_key={"orphan": 1},
        )
        with pytest.raises(IllegalGameActionError, match="périmètre"):
            cast_spell_from_hand(
                state,
                rules,
                caster_player_index=0,
                spell_hand_object_id=hid,
                targets=(),
            )


class TestSpellCastServiceTiming:
    """Fenêtres rituelles vs éphémères."""

    def test_sorcery_refused_outside_main(self) -> None:
        """Rituel hors principale refusé."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.UPKEEP))
        hid = state.issue_object_id()
        state.register_object_at(
            InGameCard(hid, CardReference("golem")),
            ZoneLocation(0, ZoneType.HAND),
        )
        state.players[0].add_floating_mana(3)
        rules = _catalog_golem()
        with pytest.raises(IllegalGameActionError, match="rituelle"):
            cast_spell_from_hand(
                state,
                rules,
                caster_player_index=0,
                spell_hand_object_id=hid,
                targets=(),
            )

    def test_instant_allowed_while_stack_nonempty(self) -> None:
        """Éphémère lançable avec priorité même si la pile n'est pas vide."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        other = state.issue_object_id()
        state.register_object_at(
            SpellOnStack(other, CardReference("dummy")),
            ZoneLocation(None, ZoneType.STACK),
        )
        bolt_hand = state.issue_object_id()
        state.register_object_at(
            InGameCard(bolt_hand, CardReference("bolt")),
            ZoneLocation(0, ZoneType.HAND),
        )
        state.players[0].add_floating_mana(2)
        rules = InMemoryCardCatalogAdapter(
            frozenset({"bolt"}),
            instant_spell_keys=frozenset({"bolt"}),
            spell_mana_cost_by_key={"bolt": 1},
            spell_target_kind_by_key={"bolt": "player"},
            spell_damage_to_player_by_key={"bolt": 2},
        )
        cast_spell_from_hand(
            state,
            rules,
            caster_player_index=0,
            spell_hand_object_id=bolt_hand,
            targets=(SimpleTarget.for_player(1),),
        )
        assert len(state.stack_zone.object_ids()) == 2
