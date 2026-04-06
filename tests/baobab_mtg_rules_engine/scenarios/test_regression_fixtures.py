"""Scénarios figés de non-régression (replay + trace)."""

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.observability.game_state_inspector import GameStateInspector
from baobab_mtg_rules_engine.replay.game_replay_service import GameReplayService
from baobab_mtg_rules_engine.replay.recorded_game_action import RecordedGameAction
from baobab_mtg_rules_engine.scenarios.scenario_builder import ScenarioBuilder
from baobab_mtg_rules_engine.scenarios.scenario_context import ScenarioContext


# Scénario minimal documenté : jouer un terrain depuis la main en principale 1.
REGRESSION_LAND_STEPS: tuple[RecordedGameAction, ...] = (
    RecordedGameAction.play_land(object_alias="forest_a"),
)


def _build_regression_land_context() -> ScenarioContext:
    rules = InMemoryCardCatalogAdapter(
        frozenset({"forest"}),
        land_keys=frozenset({"forest"}),
    )
    b = ScenarioBuilder(rules)
    b.with_two_player_game()
    b.with_turn_state(TurnState(0, 1, Step.MAIN_PRECOMBAT))
    b.with_priority_player(0)
    b.add_card_in_hand(0, "forest", alias="forest_a")
    return b.build()


class TestRegressionReplayFixtures:
    """Jeux d'instructions stables pour CI."""

    def test_land_scenario_event_count_stable(self) -> None:
        """Nombre d'événements après le scénario « land » (garde-fou non-régression)."""
        ctx = _build_regression_land_context()
        GameReplayService().replay_all(ctx, REGRESSION_LAND_STEPS)
        trace = GameStateInspector.event_trace_tuple(ctx.state)
        assert len(trace) >= 3
        assert any(name == EventType.LAND_PLAYED.name for name, _ in trace)
