"""Application d'une séquence d'actions enregistrées et vérification de déterminisme."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from baobab_mtg_rules_engine.actions.game_action import GameAction
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.observability.game_state_inspector import GameStateInspector
from baobab_mtg_rules_engine.replay.recorded_game_action import (
    RecordedGameAction,
    resolve_to_game_action,
)
from baobab_mtg_rules_engine.scenarios.scenario_context import ScenarioContext


class GameReplayService:
    """Rejoue des :class:`RecordedGameAction` et compare des traces d'événements."""

    def apply_step(self, context: ScenarioContext, recorded: RecordedGameAction) -> None:
        """Résout une instruction puis l'applique via le service légal.

        :raises ReplaySequenceError: si la résolution ou la légalité échoue.
        """
        action = resolve_to_game_action(recorded, object_aliases=context.object_aliases)
        self._apply_game_action(context, action)

    def replay_all(self, context: ScenarioContext, steps: Sequence[RecordedGameAction]) -> None:
        """Applique une séquence d'instructions dans l'ordre."""
        for step in steps:
            self.apply_step(context, step)

    def assert_replay_produces_event_trace(
        self,
        build_context: Callable[[], ScenarioContext],
        steps: Sequence[RecordedGameAction],
        *,
        expected_trace: tuple[tuple[str, tuple[tuple[str, str | int], ...]], ...],
    ) -> None:
        """Vérifie qu'un scénario rejoué produit exactement la trace d'événements attendue.

        :raises AssertionError: si la trace diffère.
        """
        ctx = build_context()
        self.replay_all(ctx, steps)
        actual = GameStateInspector.event_trace_tuple(ctx.state)
        if actual != expected_trace:
            msg = f"Trace observée {actual!r} != attendue {expected_trace!r}"
            raise AssertionError(msg)

    def assert_deterministic_across_replays(
        self,
        build_context: Callable[[], ScenarioContext],
        steps: Sequence[RecordedGameAction],
    ) -> None:
        """Deux exécutions depuis des contextes neufs doivent produire la même trace d'événements.

        :raises AssertionError: si le moteur n'est pas déterministe pour ce scénario.
        """
        first = build_context()
        self.replay_all(first, steps)
        second = build_context()
        self.replay_all(second, steps)
        t1 = GameStateInspector.event_trace_tuple(first.state)
        t2 = GameStateInspector.event_trace_tuple(second.state)
        if t1 != t2:
            msg = f"Non-déterminisme détecté : {t1!r} vs {t2!r}"
            raise AssertionError(msg)

    @staticmethod
    def record_from_game_action(
        action: GameAction,
        *,
        id_to_alias: dict[int, str],
    ) -> RecordedGameAction:
        """Enregistre une action jouée pour export (round-trip avec ``object_aliases``).

        :raises ReplaySequenceError: si l'action n'est pas sérialisable.
        """
        return RecordedGameAction.from_game_action(action, id_to_alias=id_to_alias)

    @staticmethod
    def _apply_game_action(context: ScenarioContext, action: GameAction) -> None:
        context.legal_service.apply_action(
            context.state,
            context.rules,
            context.acting_player_index,
            action,
            context.turn_manager,
        )

    @staticmethod
    def supported_event_types_for_docs() -> tuple[str, ...]:
        """:return: Noms des membres de :class:`EventType` (aperçu documentation)."""
        return tuple(sorted(EventType.__members__.keys()))
