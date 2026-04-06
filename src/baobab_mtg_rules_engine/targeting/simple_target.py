"""Cible simple pour sorts à ciblage restreint (joueur ou permanent)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


@dataclass(frozen=True, slots=True)
class SimpleTarget:
    """Exactement un joueur (index 0/1) **ou** un permanent sur le champ de bataille."""

    player_index: int | None
    permanent_object_id: GameObjectId | None

    def __post_init__(self) -> None:
        has_player = self.player_index is not None
        has_perm = self.permanent_object_id is not None
        if has_player == has_perm:
            msg = "Une cible simple doit être soit un joueur, soit un permanent, exclusivement."
            raise ValueError(msg)
        if has_player:
            idx = self.player_index
            if idx is None:
                msg = "Invariant : cible joueur sans index."
                raise ValueError(msg)
            if idx not in (0, 1):
                msg = "L'index joueur d'une cible doit être 0 ou 1 dans ce moteur duel."
                raise ValueError(msg)

    @classmethod
    def for_player(cls, player_index: int) -> SimpleTarget:
        """Construit une cible joueur."""
        return cls(player_index=player_index, permanent_object_id=None)

    @classmethod
    def for_permanent(cls, permanent_object_id: GameObjectId) -> SimpleTarget:
        """Construit une cible permanent (identifiant d'objet)."""
        return cls(player_index=None, permanent_object_id=permanent_object_id)

    def sort_key(self) -> tuple[Any, ...]:
        """:return: Clé de tri déterministe (joueur avant permanent, puis identifiants)."""
        if self.player_index is not None:
            return ("player", self.player_index)
        perm = self.permanent_object_id
        if perm is None:
            msg = "Invariant : cible permanent sans identifiant."
            raise ValueError(msg)
        return ("permanent", perm.value)
