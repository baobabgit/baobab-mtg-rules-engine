"""Tests pour :class:`TurnManager`."""

import pytest

from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.engine.turn_manager import TurnManager
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError
from baobab_mtg_rules_engine.exceptions.validation_exception import ValidationException


class _FailingLegalityPort:
    """Port de légalité factice qui échoue toujours (ordre validation / mutation)."""

    def assert_legal_priority_window(self, state: GameState, priority_player_index: int) -> None:
        """Lève :class:`ValidationException` sans considérer les arguments."""
        _ = (state, priority_player_index)
        msg = "fenêtre illégale"
        raise ValidationException(msg, field_name="priority")


class TestTurnManager:
    """Progression de tour, saut de pioche et nettoyage."""

    def test_open_step_chains_untap_to_upkeep(self) -> None:
        """UNTAP mène immédiatement à UPKEEP avec priorité au joueur actif."""
        state = GameState.new_two_player()
        mgr = TurnManager(state)
        mgr.open_current_step()
        assert state.turn_state.step is Step.UPKEEP
        assert state.priority_player_index == state.turn_state.active_player_index

    def test_priority_alternates_before_step_advance_empty_stack(self) -> None:
        """À pile vide, AP puis NAP passent puis l'étape avance."""
        state = GameState.new_two_player()
        mgr = TurnManager(state)
        mgr.open_current_step()
        assert state.turn_state.step is Step.UPKEEP
        mgr.pass_priority()
        assert state.priority_player_index == 1
        mgr.pass_priority()
        # Le moteur avance l'étape : mypy ne suit pas les mutations via ``pass_priority``.
        assert state.turn_state.step == Step.DRAW  # type: ignore[comparison-overlap]

    def test_first_duel_turn_draw_skipped_for_opening_player(self) -> None:
        """Le premier tour du joueur qui commence saute la pioche (CR 103.8 simplifié)."""
        state = GameState.new_two_player()
        state.establish_duel_opening_player(0)
        mgr = TurnManager(state)
        mgr.open_current_step()
        hand_before = len(state.players[0].zone(ZoneType.HAND).object_ids())
        lib_before = len(state.players[0].zone(ZoneType.LIBRARY).object_ids())
        for _ in range(2):
            mgr.pass_priority()
        assert state.turn_state.step == Step.DRAW
        assert EventType.TURN_DRAW_STEP_SKIPPED_FIRST_DUEL_TURN in [
            e.event_type for e in state.events
        ]
        assert len(state.players[0].zone(ZoneType.HAND).object_ids()) == hand_before
        assert len(state.players[0].zone(ZoneType.LIBRARY).object_ids()) == lib_before

    def test_first_duel_turn_draw_skipped_when_player_one_starts(self) -> None:
        """Si le joueur 1 commence, le saut de pioche le concerne lui au tour 1."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(1, 1, Step.UNTAP))
        state.establish_duel_opening_player(1)
        mgr = TurnManager(state)
        mgr.open_current_step()
        for _ in range(2):
            mgr.pass_priority()
        assert state.turn_state.step == Step.DRAW
        assert EventType.TURN_DRAW_STEP_SKIPPED_FIRST_DUEL_TURN in [
            e.event_type for e in state.events
        ]

    def test_later_turn_performs_normal_draw(self) -> None:
        """Hors premier tour du duel, l'étape de pioche retire une carte de la bibliothèque."""
        state = GameState.new_two_player()
        state.establish_duel_opening_player(0)
        lib = ZoneLocation(0, ZoneType.LIBRARY)
        for i in range(3):
            cid = state.issue_object_id()
            state.register_object_at(InGameCard(cid, CardReference(f"c{i}")), lib)
        state.replace_turn_state(TurnState(0, 3, Step.DRAW))
        mgr = TurnManager(state)
        mgr.open_current_step()
        assert EventType.TURN_DRAW_PERFORMED in [e.event_type for e in state.events]
        assert len(state.players[0].zone(ZoneType.HAND).object_ids()) == 1

    def test_cleanup_clears_floating_mana(self) -> None:
        """Le nettoyage vide le mana résiduel et enregistre l'événement."""
        state = GameState.new_two_player()
        state.players[0].add_floating_mana(3)
        state.replace_turn_state(TurnState(0, 1, Step.CLEANUP))
        mgr = TurnManager(state)
        mgr.open_current_step()
        assert state.players[0].floating_mana == 0
        assert EventType.FLOATING_MANA_CLEARED in [e.event_type for e in state.events]

    def test_full_turn_emits_step_and_roll_events(self) -> None:
        """Un tour complet laisse une trace d'étapes et de passage au joueur suivant."""
        state = GameState.new_two_player()
        mgr = TurnManager(state)
        mgr.open_current_step()
        safety = 0
        while state.turn_state.active_player_index == 0 and safety < 200:
            mgr.pass_priority()
            safety += 1
        assert state.turn_state.active_player_index == 1
        assert state.turn_state.turn_number == 2
        assert EventType.TURN_ROLLED_TO_NEXT_PLAYER in [e.event_type for e in state.events]
        assert sum(1 for e in state.events if e.event_type is EventType.TURN_STEP_ENTERED) >= 10

    def test_advance_from_cleanup_step_raises(self) -> None:
        """Le nettoyage ne se termine pas par passes : avancer depuis CLEANUP est incohérent."""
        state = GameState.new_two_player()
        state.replace_turn_state(TurnState(0, 1, Step.CLEANUP))
        mgr = TurnManager(state)
        with pytest.raises(InvalidGameStateError, match="priorité"):
            mgr._advance_step_after_priority_window()  # pylint: disable=protected-access

    def test_legality_checked_before_pass_mutation(self) -> None:
        """Une légalité en échec empêche la passe (pas d'événement PRIORITY_PASSED)."""
        state = GameState.new_two_player()
        mgr = TurnManager(state, legality=_FailingLegalityPort())
        mgr.open_current_step()
        count_before = len(state.events)
        with pytest.raises(ValidationException, match="fenêtre"):
            mgr.pass_priority()
        assert len(state.events) == count_before
        assert all(
            e.event_type is not EventType.PRIORITY_PASSED for e in state.events[count_before:]
        )
