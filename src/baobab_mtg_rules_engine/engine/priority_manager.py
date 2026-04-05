"""Rotation de priorité et comptage des passes à pile vide (duel)."""

from baobab_mtg_rules_engine.domain.game_state import GameState


class PriorityManager:
    """Gère la priorité et les passes consécutives lorsque la pile est vide.

    :param state: État de partie (deux joueurs) inspecté et mis à jour via l'API moteur.
    """

    def __init__(self, state: GameState) -> None:
        self._state: GameState = state

    def assign_to_active_player(self) -> None:
        """Donne la priorité au joueur actif et remet le compteur de passes à zéro."""
        self._state.turn_engine_set_priority_player(self._state.turn_state.active_player_index)
        self._state.turn_engine_reset_empty_stack_passes()

    def process_priority_pass(self) -> bool:
        """Applique une passe du détenteur actuel de la priorité.

        :return: ``True`` si l'étape doit avancer (pile vide et deux passes consécutives).
        """
        stack_empty = len(self._state.stack_zone.object_ids()) == 0
        if not stack_empty:
            self._rotate_priority()
            self._state.turn_engine_reset_empty_stack_passes()
            return False
        count = self._state.turn_engine_increment_empty_stack_passes()
        if count >= 2:
            self._state.turn_engine_reset_empty_stack_passes()
            return True
        self._rotate_priority()
        return False

    def _rotate_priority(self) -> None:
        current = self._state.priority_player_index
        self._state.turn_engine_set_priority_player(1 - current)
