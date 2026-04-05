"""État de tour : joueur actif, numéro de tour et étape."""

from __future__ import annotations

from dataclasses import dataclass

from baobab_mtg_rules_engine.domain.phase import Phase
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError


@dataclass(frozen=True, slots=True)
class TurnState:
    """Snapshot immuable du tour en cours.

    La :attr:`phase` est dérivée de :attr:`step` pour éviter les incohérences.

    :param active_player_index: Joueur dont c'est le tour.
    :param turn_number: Numéro de tour (commence à 1).
    :param step: Étape détaillée en cours.
    """

    active_player_index: int
    turn_number: int
    step: Step

    def __post_init__(self) -> None:
        if self.active_player_index < 0:
            msg = "active_player_index ne peut pas être négatif."
            raise InvalidGameStateError(msg, field_name="active_player_index")
        if self.turn_number < 1:
            msg = "turn_number doit être au moins 1."
            raise InvalidGameStateError(msg, field_name="turn_number")

    @property
    def phase(self) -> Phase:
        """:return: Phase MTG dérivée de :attr:`step`."""
        return self.step.phase()

    @classmethod
    def start_first_turn(cls, starting_player_index: int = 0) -> TurnState:
        """Construit le tour initial (étape défausse / untap selon conventions du moteur).

        Ici le tour démarre à l'étape ``UNTAP`` du joueur 0 par défaut.

        :param starting_player_index: Joueur qui commence (0 ou 1 en deux joueurs).
        :return: État de tour initial.
        """
        if starting_player_index < 0:
            msg = "starting_player_index ne peut pas être négatif."
            raise InvalidGameStateError(msg, field_name="starting_player_index")
        return cls(
            active_player_index=starting_player_index,
            turn_number=1,
            step=Step.UNTAP,
        )
