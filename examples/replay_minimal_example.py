"""Exemple reproductible : scénario minimal + replay + inspection du journal.

Exécution : ``python examples/replay_minimal_example.py`` depuis la racine du dépôt
avec le package installé (``pip install -e .``).
"""

from __future__ import annotations

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


def main() -> None:
    """Construit un duel avec une Forêt en main, rejoue PLAY_LAND et affiche la trace."""
    rules = InMemoryCardCatalogAdapter(
        frozenset({"forest"}),
        land_keys=frozenset({"forest"}),
    )
    ctx = (
        ScenarioBuilder(rules)
        .with_two_player_game()
        .with_turn_state(TurnState(0, 1, Step.MAIN_PRECOMBAT))
        .with_priority_player(0)
        .add_card_in_hand(0, "forest", alias="f1")
        .build()
    )
    steps = (RecordedGameAction.play_land(object_alias="f1"),)
    GameReplayService().replay_all(ctx, steps)
    trace = GameStateInspector.event_trace_tuple(ctx.state)
    print(GameStateInspector.snapshot_summary(ctx.state))
    print(GameStateInspector.format_events(ctx.state, max_entries=12))
    assert any(e[0] == EventType.LAND_PLAYED.name for e in trace), trace


if __name__ == "__main__":
    main()
