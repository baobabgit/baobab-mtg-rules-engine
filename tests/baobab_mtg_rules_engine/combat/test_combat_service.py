"""Tests pour :class:`CombatService`."""

import pytest

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.combat.combat_service import CombatService
from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.engine.state_based_action_service import StateBasedActionService
from baobab_mtg_rules_engine.exceptions.illegal_game_action_error import IllegalGameActionError


def _rules_two_creatures() -> InMemoryCardCatalogAdapter:
    keys = frozenset({"a", "b"})
    return InMemoryCardCatalogAdapter(
        keys,
        creature_keys=keys,
        creature_power_toughness_by_key={"a": (3, 3), "b": (2, 2)},
    )


class TestCombatServiceUnblocked:
    """Dégâts directs au joueur défenseur."""

    def test_unblocked_attacker_damages_defending_player(self) -> None:
        """La force de l'attaquant est infligée au joueur adverse."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.COMBAT_DAMAGE))
        aid = state.issue_object_id()
        state.register_object_at(
            Permanent(aid, CardReference("a")),
            ZoneLocation(0, ZoneType.BATTLEFIELD),
        )
        state.apply_declare_attacker(0, aid)
        rules = _rules_two_creatures()
        life_before = state.players[1].life_total
        CombatService().resolve_combat_damage_step(state, rules)
        assert state.players[1].life_total == life_before - 3
        assert EventType.COMBAT_DAMAGE_ASSIGNED in [e.event_type for e in state.events]
        assert EventType.PLAYER_DAMAGED in [e.event_type for e in state.events]


class TestCombatServiceBlocked:
    """Échange de blessures créature contre créature."""

    def test_blocked_creatures_exchange_damage(self) -> None:
        """Chaque créature marque les dégâts égaux à la force adverse."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.COMBAT_DAMAGE))
        attacker = state.issue_object_id()
        blocker = state.issue_object_id()
        state.register_object_at(
            Permanent(attacker, CardReference("a")),
            ZoneLocation(0, ZoneType.BATTLEFIELD),
        )
        state.register_object_at(
            Permanent(blocker, CardReference("b")),
            ZoneLocation(1, ZoneType.BATTLEFIELD),
        )
        state.apply_declare_attacker(0, attacker)
        state.apply_declare_blocker(1, blocker, attacker)
        rules = _rules_two_creatures()
        CombatService().resolve_combat_damage_step(state, rules)
        aobj = state.get_object(attacker)
        blobj = state.get_object(blocker)
        assert isinstance(aobj, Permanent)
        assert isinstance(blobj, Permanent)
        assert aobj.marked_damage == 2
        assert blobj.marked_damage == 3


class TestCombatServiceLethal:
    """Destruction après ABS."""

    def test_lethal_damage_sends_creature_to_graveyard(self) -> None:
        """Blessures >= endurance : défausse via ABS."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.COMBAT_DAMAGE))
        attacker = state.issue_object_id()
        blocker = state.issue_object_id()
        state.register_object_at(
            Permanent(attacker, CardReference("a")),
            ZoneLocation(0, ZoneType.BATTLEFIELD),
        )
        state.register_object_at(
            Permanent(blocker, CardReference("b")),
            ZoneLocation(1, ZoneType.BATTLEFIELD),
        )
        state.apply_declare_attacker(0, attacker)
        state.apply_declare_blocker(1, blocker, attacker)
        keys = frozenset({"a", "b"})
        rules = InMemoryCardCatalogAdapter(
            keys,
            creature_keys=keys,
            creature_power_toughness_by_key={"a": (2, 2), "b": (2, 2)},
        )
        CombatService().resolve_combat_damage_step(state, rules)
        StateBasedActionService().apply_all(state, rules)
        assert state.find_location(attacker).zone_type is ZoneType.GRAVEYARD
        assert state.find_location(blocker).zone_type is ZoneType.GRAVEYARD
        assert EventType.CREATURE_DESTROYED in [e.event_type for e in state.events]


class TestCombatServiceMultiBlockRejected:
    """Plus d'un bloqueur par attaquant."""

    def test_two_blockers_same_attacker_raises(self) -> None:
        """Configuration hors périmètre refusée à la résolution."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.COMBAT_DAMAGE))
        a = state.issue_object_id()
        b1 = state.issue_object_id()
        b2 = state.issue_object_id()
        for oid, key in ((a, "a"), (b1, "b"), (b2, "b")):
            state.register_object_at(
                Permanent(oid, CardReference(key)),
                ZoneLocation(0 if oid == a else 1, ZoneType.BATTLEFIELD),
            )
        state.apply_declare_attacker(0, a)
        state.apply_declare_blocker(1, b1, a)
        # Contourner la validation de haut niveau pour simuler un état illégal futur.
        state._declared_blocks.append((b2, a))  # pylint: disable=protected-access
        rules = _rules_two_creatures()
        with pytest.raises(IllegalGameActionError, match="bloqueur"):
            CombatService().resolve_combat_damage_step(state, rules)
