"""Rotation de priorité et comptage des passes à pile vide (duel)."""

from baobab_mtg_rules_engine.domain.game_state import GameState


class PriorityManager:
    """Gère la priorité et les passes consécutives lorsque la pile est vide.

    :param state: État de partie (deux joueurs) inspecté et mis à jour via l'API moteur.
    """

    def __init__(
        self,
        state: GameState,
        *,
        close_non_empty_window: bool = False,
    ) -> None:
        self._state: GameState = state
        self._close_non_empty_window: bool = close_non_empty_window

    def assign_to_active_player(self) -> None:
        """Donne la priorité au joueur actif et remet le compteur de passes à zéro."""
        self.assign_to_player(self._state.turn_state.active_player_index)

    def assign_to_player(self, player_index: int) -> None:
        """Donne la priorité au joueur indiqué et remet les compteurs de passe à zéro."""
        self._state.turn_engine_set_priority_player(player_index)
        self._state.turn_engine_reset_empty_stack_passes()
        self._state.turn_engine_reset_non_empty_stack_passes()

    def process_priority_pass(self) -> bool:
        """Applique une passe du détenteur actuel de la priorité.

        :return: ``True`` si la fenêtre se ferme après deux passes consécutives.
        """
        stack_empty = len(self._state.stack_zone.object_ids()) == 0
        if not stack_empty:
            if not self._close_non_empty_window:
                self._state.turn_engine_reset_empty_stack_passes()
                self._state.turn_engine_reset_non_empty_stack_passes()
                self._rotate_priority()
                return False
            self._state.turn_engine_reset_empty_stack_passes()
            count = self._state.turn_engine_increment_non_empty_stack_passes()
            if count >= 2:
                self._state.turn_engine_reset_non_empty_stack_passes()
                return True
            self._rotate_priority()
            return False
        self._state.turn_engine_reset_non_empty_stack_passes()
        count = self._state.turn_engine_increment_empty_stack_passes()
        if count >= 2:
            self._state.turn_engine_reset_empty_stack_passes()
            return True
        self._rotate_priority()
        return False

    def _rotate_priority(self) -> None:
        current = self._state.priority_player_index
        self._state.turn_engine_set_priority_player(1 - current)
