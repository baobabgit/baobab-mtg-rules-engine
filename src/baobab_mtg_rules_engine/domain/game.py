"""Partie : identifiant de session et état de jeu courant."""

from __future__ import annotations

from dataclasses import dataclass

from baobab_mtg_rules_engine.domain.game_state import GameState


@dataclass
class Game:
    """Regroupe l'identité d'une session et son :class:`GameState` inspectable.

    :param game_id: Identifiant stable de session (hors moteur de règles).
    :param state: État de jeu courant.
    """

    game_id: str
    state: GameState

    @classmethod
    def create_two_player(
        cls,
        game_id: str,
        *,
        names: tuple[str, str] | None = None,
        life_totals: tuple[int, int] | None = None,
    ) -> Game:
        """Construit une partie à deux joueurs avec état initial standard.

        :param game_id: Identifiant de session.
        :param names: Noms des joueurs (voir :meth:`GameState.new_two_player`).
        :param life_totals: Points de vie initiaux.
        :return: Instance de :class:`Game` prête à l'emploi.
        """
        state = GameState.new_two_player(names=names, life_totals=life_totals)
        return cls(game_id=game_id, state=state)
