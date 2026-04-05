"""Port de validation de légalité avant attribution effective de la priorité."""

from typing import Protocol, runtime_checkable

from baobab_mtg_rules_engine.domain.game_state import GameState


@runtime_checkable
class PriorityActionLegalityPort(Protocol):
    """Vérifie qu'une fenêtre de priorité peut s'ouvrir pour le joueur indiqué.

    Appelé avant toute mutation liée à une passe ; en cas d'échec, lever
    :class:`~baobab_mtg_rules_engine.exceptions.validation_exception.ValidationException`.
    """

    def assert_legal_priority_window(self, state: GameState, priority_player_index: int) -> None:
        """Valide l'état pour le joueur qui s'apprête à agir ou passer.

        :param state: État courant (lecture seule attendue).
        :param priority_player_index: Joueur concerné par la priorité.
        """
