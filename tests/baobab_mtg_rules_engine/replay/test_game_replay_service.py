"""Tests pour :class:`GameReplayService`."""

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.observability.game_state_inspector import GameStateInspector
from baobab_mtg_rules_engine.actions.play_land_action import PlayLandAction
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.replay.game_replay_service import GameReplayService
from baobab_mtg_rules_engine.replay.recorded_game_action import RecordedGameAction
from baobab_mtg_rules_engine.scenarios.scenario_builder import ScenarioBuilder
from baobab_mtg_rules_engine.scenarios.scenario_context import ScenarioContext


def _rules_forest() -> InMemoryCardCatalogAdapter:
    return InMemoryCardCatalogAdapter(
        frozenset({"forest"}),
        land_keys=frozenset({"forest"}),
    )


def _build_land_play_context() -> ScenarioContext:
    b = ScenarioBuilder(_rules_forest())
    b.with_two_player_game()
    b.with_turn_state(TurnState(0, 1, Step.MAIN_PRECOMBAT))
    b.with_priority_player(0)
    b.add_card_in_hand(0, "forest", alias="f1")
    return b.build()


class TestGameReplayService:
    """Replay déterministe et vérification de trace."""

    def test_replay_play_land_is_deterministic(self) -> None:
        """Deux replays identiques produisent la même trace d'événements."""
        steps = (RecordedGameAction.play_land(object_alias="f1"),)
        GameReplayService().assert_deterministic_across_replays(
            lambda: _build_land_play_context(),
            steps,
        )

    def test_replay_play_land_mutates_state(self) -> None:
        """Après replay, le terrain est au champ."""
        ctx = _build_land_play_context()
        GameReplayService().replay_all(ctx, (RecordedGameAction.play_land(object_alias="f1"),))
        from baobab_mtg_rules_engine.domain.zone_type import ZoneType

        ids = ctx.state.players[0].zone(ZoneType.BATTLEFIELD).object_ids()
        assert len(ids) == 1
        assert EventType.LAND_PLAYED in [e.event_type for e in ctx.state.events]

    def test_assert_event_trace_subset_matches(self) -> None:
        """La trace complète contient les événements attendus en fin de séquence."""
        ctx = _build_land_play_context()
        GameReplayService().replay_all(ctx, (RecordedGameAction.play_land(object_alias="f1"),))
        trace = GameStateInspector.event_trace_tuple(ctx.state)
        assert any(t[0] == EventType.LAND_PLAYED.name for t in trace)

    def test_record_from_game_action_delegates(self) -> None:
        """L'enregistrement via le service délègue à :class:`RecordedGameAction`."""
        oid = GameObjectId(99)
        rec = GameReplayService.record_from_game_action(
            PlayLandAction(oid),
            id_to_alias={oid.value: "z"},
        )
        assert rec.kind == "PLAY_LAND"
