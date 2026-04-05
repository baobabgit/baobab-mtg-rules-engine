"""Tests pour :class:`LegalActionService`."""

from __future__ import annotations

import typing
from typing import Any
from unittest.mock import patch

import pytest

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
from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.spell_on_stack import SpellOnStack
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.engine.legal_action_service import LegalActionService
from baobab_mtg_rules_engine.engine.turn_manager import TurnManager
from baobab_mtg_rules_engine.exceptions.illegal_game_action_error import IllegalGameActionError


def _catalog_with_gameplay() -> InMemoryCardCatalogAdapter:
    supported = frozenset({"forest", "bear", "sorcery1", "instant1", "rock"})
    return InMemoryCardCatalogAdapter(
        supported,
        land_keys=frozenset({"forest"}),
        creature_keys=frozenset({"bear", "rock"}),
        sorcery_spell_keys=frozenset({"sorcery1"}),
        instant_spell_keys=frozenset({"instant1"}),
        spell_mana_cost_by_key={"sorcery1": 1, "instant1": 1},
        activated_ability_costs_by_key={"rock": (1, 2)},
    )


def _register_hand_land(state: GameState, player: int, key: str = "forest") -> GameObjectId:
    oid = state.issue_object_id()
    state.register_object_at(
        InGameCard(oid, CardReference(key)), ZoneLocation(player, ZoneType.HAND)
    )
    return oid


def _register_hand_spell(state: GameState, player: int, key: str) -> GameObjectId:
    oid = state.issue_object_id()
    state.register_object_at(
        InGameCard(oid, CardReference(key)), ZoneLocation(player, ZoneType.HAND)
    )
    return oid


def _register_battlefield_creature(
    state: GameState, player: int, key: str = "bear"
) -> GameObjectId:
    oid = state.issue_object_id()
    state.register_object_at(
        Permanent(oid, CardReference(key)), ZoneLocation(player, ZoneType.BATTLEFIELD)
    )
    return oid


class TestLegalActionServicePriority:
    """Priorité et refus hors fenêtre."""

    def test_compute_requires_holding_priority(self) -> None:
        """Un joueur sans priorité ne peut pas interroger les actions légales."""
        state = GameState.new_two_player()
        state.turn_engine_set_priority_player(1)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        with pytest.raises(IllegalGameActionError, match="priorité"):
            svc.compute_legal_actions(state, rules, acting_player_index=0)

    def test_apply_rejects_wrong_player_even_if_action_is_pass(self) -> None:
        """La tentative d'application sans priorité est refusée avant mutation."""
        state = GameState.new_two_player()
        state.turn_engine_set_priority_player(0)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        tm = TurnManager(state)
        with pytest.raises(IllegalGameActionError, match="priorité"):
            svc.apply_action(state, rules, 1, PassPriorityAction(), tm)


class TestLegalActionServicePhasesAndLands:
    """Timing rituel, terrains et stabilité."""

    def test_play_land_only_main_phase_empty_stack_active_player(self) -> None:
        """Le terrain est proposé en principale active, pile vide."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        _register_hand_land(state, 0)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        legal = svc.compute_legal_actions(state, rules, 0)
        kinds = [a.kind for a in legal]
        assert SupportedActionKind.PLAY_LAND in kinds

    def test_play_land_refused_outside_main(self) -> None:
        """Hors principale, aucun terrain n'est listé."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.DRAW))
        state.turn_engine_set_priority_player(0)
        _register_hand_land(state, 0)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        legal = svc.compute_legal_actions(state, rules, 0)
        assert all(a.kind is not SupportedActionKind.PLAY_LAND for a in legal)

    def test_second_land_same_turn_not_listed_after_first_played(self) -> None:
        """Après un terrain, un second terrain légal en main n'apparaît plus."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        first = _register_hand_land(state, 0)
        _register_hand_land(state, 0)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        before = svc.compute_legal_actions(state, rules, 0)
        assert sum(1 for a in before if isinstance(a, PlayLandAction)) == 2
        state.apply_play_land(0, first)
        after = svc.compute_legal_actions(state, rules, 0)
        assert all(not isinstance(a, PlayLandAction) for a in after)

    def test_legal_list_is_stable_between_calls(self) -> None:
        """Même état → même tuple d'actions (ordre inclus)."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        _register_hand_land(state, 0)
        _register_hand_spell(state, 0, "sorcery1")
        state.players[0].add_floating_mana(3)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        a = svc.compute_legal_actions(state, rules, 0)
        b = svc.compute_legal_actions(state, rules, 0)
        assert a == b


class TestLegalActionServiceSorceryInstant:
    """Rituels (pile vide, principale) contre instants."""

    def test_sorcery_refused_when_stack_not_empty(self) -> None:
        """Un rituel n'est pas listé si la pile n'est pas vide."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        sorcery_oid = _register_hand_spell(state, 0, "sorcery1")
        state.players[0].add_floating_mana(2)
        stack_id = state.issue_object_id()
        state.register_object_at(
            SpellOnStack(stack_id, CardReference("instant1")),
            ZoneLocation(None, ZoneType.STACK),
        )
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        legal = svc.compute_legal_actions(state, rules, 0)
        assert CastSpellAction(sorcery_oid) not in legal

    def test_instant_allowed_when_stack_not_empty(self) -> None:
        """Un instant reste listé avec priorité même si la pile contient un sort."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        spell_oid = _register_hand_spell(state, 0, "instant1")
        state.players[0].add_floating_mana(2)
        stack_id = state.issue_object_id()
        state.register_object_at(
            SpellOnStack(stack_id, CardReference("sorcery1")),
            ZoneLocation(None, ZoneType.STACK),
        )
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        legal = svc.compute_legal_actions(state, rules, 0)
        assert CastSpellAction(spell_oid) in legal

    def test_sorcery_refused_for_non_active_even_with_priority(self) -> None:
        """Le NAP avec priorité ne voit pas les rituels de sa main en principale adverse."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(1)
        _register_hand_spell(state, 1, "sorcery1")
        state.players[1].add_floating_mana(2)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        legal = svc.compute_legal_actions(state, rules, 1)
        for a in legal:
            if isinstance(a, CastSpellAction):
                hand_card = typing.cast(
                    InGameCard,
                    state.get_object(a.spell_object_id),
                )
                assert hand_card.card_reference.catalog_key != "sorcery1"


class TestLegalActionServiceApplyAndCombat:
    """Application sans ensemble légal et combat simplifié."""

    def test_apply_rejects_action_not_in_legal_set(self) -> None:
        """Une action fabriquée hors liste courante est refusée."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        bogus = GameObjectId(99)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        tm = TurnManager(state)
        with pytest.raises(IllegalGameActionError, match="ensemble légal"):
            svc.apply_action(state, rules, 0, PlayLandAction(bogus), tm)

    def test_apply_pass_delegates_to_turn_manager(self) -> None:
        """Passer appelle :meth:`TurnManager.pass_priority` sans autre mutation métier."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.UPKEEP))
        state.turn_engine_set_priority_player(0)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        tm = TurnManager(state)
        tm.open_current_step()
        before = len(state.events)
        svc.apply_action(state, rules, 0, PassPriorityAction(), tm)
        assert len(state.events) > before

    def test_declare_attacker_only_in_declare_step(self) -> None:
        """Les attaquants n'apparaissent qu'à l'étape dédiée."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        _register_battlefield_creature(state, 0)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        assert all(
            a.kind is not SupportedActionKind.DECLARE_ATTACKER
            for a in svc.compute_legal_actions(state, rules, 0)
        )

        state.replace_turn_state(TurnState(0, 2, Step.DECLARE_ATTACKERS))
        legal = svc.compute_legal_actions(state, rules, 0)
        assert any(a.kind is SupportedActionKind.DECLARE_ATTACKER for a in legal)

    def test_declare_blocker_only_non_active_with_attackers(self) -> None:
        """Le défenseur déclare des bloqueurs sur des attaquants connus."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.DECLARE_BLOCKERS))
        attacker = _register_battlefield_creature(state, 0, "bear")
        blocker = _register_battlefield_creature(state, 1, "bear")
        state.turn_engine_set_priority_player(1)
        state.apply_declare_attacker(0, attacker)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        legal = svc.compute_legal_actions(state, rules, 1)
        assert any(
            getattr(a, "blocker_object_id", None) == blocker
            and getattr(a, "attacker_object_id", None) == attacker
            for a in legal
        )

    def test_apply_unknown_subclass_raises_even_if_marked_legal(self) -> None:
        """Branche défensive si une sous-classe :class:`GameAction` non gérée est injectée."""

        class _OddAction(GameAction):
            @property
            def kind(self) -> SupportedActionKind:
                return SupportedActionKind.PASS_PRIORITY

            def sort_key(self) -> tuple[Any, ...]:
                return (SupportedActionKind.PASS_PRIORITY.value, "odd")

        state = GameState.new_two_player()
        state.turn_engine_set_priority_player(0)
        odd = _OddAction()
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        tm = TurnManager(state)
        with patch.object(
            LegalActionService,
            "compute_legal_actions",
            return_value=(odd,),
        ):
            with pytest.raises(IllegalGameActionError, match="non géré"):
                svc.apply_action(state, rules, 0, odd, tm)


class TestLegalActionServiceApplyIntegration:
    """Application via le service après validation (couverture des branches ``apply_*``)."""

    def test_apply_play_land_moves_card(self) -> None:
        """Jouer un terrain via le service déplace la carte vers le champ."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        land_oid = _register_hand_land(state, 0)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        tm = TurnManager(state)
        play = PlayLandAction(land_oid)
        svc.apply_action(state, rules, 0, play, tm)
        assert state.find_location(land_oid).zone_type is ZoneType.BATTLEFIELD
        assert state.lands_played_this_turn == 1

    def test_apply_cast_sorcery_pays_and_puts_spell_on_stack(self) -> None:
        """Lancer un rituel paie le mana et place un objet pile."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        spell_oid = _register_hand_spell(state, 0, "sorcery1")
        state.players[0].add_floating_mana(3)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        tm = TurnManager(state)
        cast_action = CastSpellAction(spell_oid)
        svc.apply_action(state, rules, 0, cast_action, tm)
        assert state.players[0].floating_mana == 2
        assert len(state.stack_zone.object_ids()) == 1

    def test_apply_activate_simple_ability_spends_mana(self) -> None:
        """Activer une capacité simple dépense le coût indiqué par le catalogue."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        rock = _register_battlefield_creature(state, 0, "rock")
        state.players[0].add_floating_mana(2)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        tm = TurnManager(state)
        act = ActivateSimpleAbilityAction(rock, 1)
        svc.apply_action(state, rules, 0, act, tm)
        assert state.players[0].floating_mana == 1

    def test_apply_declare_attacker_registers_creature(self) -> None:
        """Déclarer un attaquant met à jour l'état de combat."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.DECLARE_ATTACKERS))
        state.turn_engine_set_priority_player(0)
        bear = _register_battlefield_creature(state, 0, "bear")
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        tm = TurnManager(state)
        dec = DeclareAttackerAction(bear)
        svc.apply_action(state, rules, 0, dec, tm)
        assert bear in state.declared_attackers

    def test_apply_declare_blocker_registers_pair(self) -> None:
        """Déclarer un bloqueur associe défenseur et attaquant."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.DECLARE_BLOCKERS))
        attacker = _register_battlefield_creature(state, 0, "bear")
        blocker = _register_battlefield_creature(state, 1, "bear")
        state.turn_engine_set_priority_player(1)
        state.apply_declare_attacker(0, attacker)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        tm = TurnManager(state)
        dec = DeclareBlockerAction(blocker, attacker)
        svc.apply_action(state, rules, 1, dec, tm)
        assert (blocker, attacker) in state.declared_blocks


class TestLegalActionServiceEdgeBranches:
    """Branches de filtrage (objets atypiques en zone, coûts négatifs)."""

    def test_spell_on_stack_in_hand_is_ignored_for_cast_legality(self) -> None:
        """Un :class:`SpellOnStack` en main n'est pas une carte lançable comme sort."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        odd = state.issue_object_id()
        state.register_object_at(
            SpellOnStack(odd, CardReference("sorcery1")),
            ZoneLocation(0, ZoneType.HAND),
        )
        _register_hand_spell(state, 0, "sorcery1")
        state.players[0].add_floating_mana(2)
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        legal = svc.compute_legal_actions(state, rules, 0)
        cast_targets: set[GameObjectId] = set()
        for a in legal:
            if isinstance(a, CastSpellAction):
                cast_targets.add(a.spell_object_id)
        assert odd not in cast_targets

    def test_negative_activation_cost_is_skipped(self) -> None:
        """Les coûts d'activation négatifs ne produisent pas d'action (périmètre non supporté)."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.MAIN_PRECOMBAT))
        state.turn_engine_set_priority_player(0)
        rock = state.issue_object_id()
        state.register_object_at(
            Permanent(rock, CardReference("rock")), ZoneLocation(0, ZoneType.BATTLEFIELD)
        )
        state.players[0].add_floating_mana(5)
        supported = frozenset({"rock"})
        rules = InMemoryCardCatalogAdapter(
            supported,
            creature_keys=frozenset({"rock"}),
            activated_ability_costs_by_key={"rock": (-1, 1)},
        )
        svc = LegalActionService()
        legal = svc.compute_legal_actions(state, rules, 0)
        costs: set[int] = set()
        for a in legal:
            if isinstance(a, ActivateSimpleAbilityAction):
                if a.permanent_object_id == rock:
                    costs.add(a.generic_mana_cost)
        assert -1 not in costs
        assert 1 in costs

    def test_in_game_card_on_battlefield_not_listed_as_attacker(self) -> None:
        """Seuls les :class:`Permanent` peuvent être proposés comme attaquants."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 2, Step.DECLARE_ATTACKERS))
        state.turn_engine_set_priority_player(0)
        oid = state.issue_object_id()
        state.register_object_at(
            InGameCard(oid, CardReference("bear")), ZoneLocation(0, ZoneType.BATTLEFIELD)
        )
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        legal = svc.compute_legal_actions(state, rules, 0)
        for a in legal:
            if isinstance(a, DeclareAttackerAction):
                assert a.creature_object_id != oid

    def test_apply_cast_rejects_spell_on_stack_even_if_injected_as_legal(self) -> None:
        """Refus si la cible du lancer n'est pas une :class:`InGameCard` « brute »."""
        state = GameState.new_two_player()
        state.turn_engine_set_priority_player(0)
        odd = state.issue_object_id()
        state.register_object_at(
            SpellOnStack(odd, CardReference("sorcery1")),
            ZoneLocation(0, ZoneType.HAND),
        )
        svc = LegalActionService()
        rules = _catalog_with_gameplay()
        tm = TurnManager(state)
        cast_action = CastSpellAction(odd)
        with patch.object(
            LegalActionService,
            "compute_legal_actions",
            return_value=(cast_action,),
        ):
            with pytest.raises(IllegalGameActionError, match="InGameCard"):
                svc.apply_action(state, rules, 0, cast_action, tm)
