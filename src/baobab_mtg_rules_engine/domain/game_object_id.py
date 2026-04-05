"""Identifiant technique stable d'un objet dans une partie."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GameObjectId:
    """Identifiant opaque et immuable pour un objet de jeu.

    Les identifiants sont émis de façon monotone par :class:`GameState` afin de
    garantir un comportement déterministe et reproductible.

    :param value: Entier strictement positif attribué par le moteur.
    """

    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            msg = "GameObjectId doit être strictement positif."
            raise ValueError(msg)
