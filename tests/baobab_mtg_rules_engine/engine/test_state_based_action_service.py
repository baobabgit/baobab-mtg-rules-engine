"""Tests pour :class:`StateBasedActionService`."""

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.engine.state_based_action_service import StateBasedActionService


class TestStateBasedActionServiceLife:
    """Défaite par points de vie."""

    def test_zero_life_assigns_winner(self) -> None:
        """Un joueur à 0 PV perd ; l'adversaire est vainqueur."""
        state = GameState.new_two_player()
        state.players[0].apply_damage(20)
        rules = InMemoryCardCatalogAdapter(frozenset())
        StateBasedActionService().apply_all(state, rules)
        assert state.winner_player_index == 1
        assert EventType.PLAYER_DEFEATED in [e.event_type for e in state.events]
        assert EventType.GAME_VICTORY_ASSIGNED in [e.event_type for e in state.events]

    def test_both_players_zero_life_is_draw(self) -> None:
        """Deux joueurs à 0 ou moins : match nul."""
        state = GameState.new_two_player()
        state.players[0].apply_damage(20)
        state.players[1].apply_damage(20)
        rules = InMemoryCardCatalogAdapter(frozenset())
        StateBasedActionService().apply_all(state, rules)
        assert state.is_draw_game
        assert state.winner_player_index is None
        assert EventType.GAME_DRAW in [e.event_type for e in state.events]


class TestStateBasedActionServiceCreature:
    """Créatures létales."""

    def test_lethal_marked_damage_destroys_creature(self) -> None:
        """Blessures marquées >= endurance : cimetière."""
        state = GameState.new_two_player()
        oid = state.issue_object_id()
        p = Permanent(oid, CardReference("grizzly"))
        p.add_marked_damage(3)
        state.register_object_at(p, ZoneLocation(0, ZoneType.BATTLEFIELD))
        rules = InMemoryCardCatalogAdapter(
            frozenset({"grizzly"}),
            creature_keys=frozenset({"grizzly"}),
            creature_power_toughness_by_key={"grizzly": (2, 2)},
        )
        StateBasedActionService().apply_all(state, rules)
        assert state.find_location(oid).zone_type is ZoneType.GRAVEYARD
