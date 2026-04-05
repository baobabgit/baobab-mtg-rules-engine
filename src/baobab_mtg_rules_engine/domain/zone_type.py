"""Types de zones reconnus par le moteur (modèle simplifié mais extensible)."""

from enum import Enum, auto


class ZoneType(Enum):
    """Zone de jeu : emplacement logique d'un objet.

    La pile est modélisée comme une zone globale sans propriétaire joueur.
    Les autres zones listées ici sont typiquement possédées par un joueur.
    """

    LIBRARY = auto()
    HAND = auto()
    GRAVEYARD = auto()
    BATTLEFIELD = auto()
    EXILE = auto()
    COMMAND = auto()
    SIDEBOARD = auto()
    STACK = auto()
