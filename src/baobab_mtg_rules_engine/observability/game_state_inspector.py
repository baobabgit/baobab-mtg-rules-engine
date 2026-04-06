"""Lecture structurée de l'état et du journal pour debug et assertions."""

from __future__ import annotations

from baobab_mtg_rules_engine.domain.game_state import GameState


class GameStateInspector:
    """Utilitaires d'inspection sans mutation (observabilité, tests, replay)."""

    @staticmethod
    def event_trace_tuple(
        state: GameState,
    ) -> tuple[tuple[str, tuple[tuple[str, str | int], ...]], ...]:
        """:return: Trace stable ``(nom d'événement, charge utile)`` pour comparaison."""
        return tuple((e.event_type.name, e.payload) for e in state.events)

    @staticmethod
    def format_events(
        state: GameState,
        *,
        max_entries: int | None = None,
    ) -> str:
        """Formate le journal sur plusieurs lignes lisibles (debug / logs).

        :param max_entries: Limite optionnelle sur le nombre de lignes (les dernières si tronqué).
        :return: Texte multi-lignes ; entrées séparées par un saut de ligne.
        """
        events = list(state.events)
        if max_entries is not None and len(events) > max_entries:
            events = events[-max_entries:]
        lines: list[str] = []
        for ev in events:
            payload_repr = ", ".join(f"{k}={v!r}" for k, v in ev.payload)
            lines.append(f"[{ev.sequence:5d}] {ev.event_type.name}  {payload_repr}")
        return "\n".join(lines)

    @staticmethod
    def snapshot_summary(state: GameState) -> str:
        """:return: Résumé condensé (priorité, étape, pile, PV)."""
        ts = state.turn_state
        p0, p1 = state.players
        stack_n = len(state.stack_zone.object_ids())
        return (
            f"priority={state.priority_player_index} "
            f"active={ts.active_player_index} step={ts.step.name} "
            f"turn={ts.turn_number} stack={stack_n} "
            f"life=({p0.life_total},{p1.life_total}) "
            f"events={len(state.events)}"
        )
