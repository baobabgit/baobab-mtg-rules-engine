"""Implémentation sans effet du port de légalité (parcours automatique, tests)."""

from baobab_mtg_rules_engine.domain.game_state import GameState


class NullPriorityActionLegalityPort:
    """N'impose aucune contrainte ; les consommateurs injectent une autre implémentation."""

    def assert_legal_priority_window(self, state: GameState, priority_player_index: int) -> None:
        """:param state: Ignoré.
        :param priority_player_index: Ignoré.
        """
        _ = (state, priority_player_index)
