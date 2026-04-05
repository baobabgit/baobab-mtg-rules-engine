"""Phases de tour Magic (structure classique du tour de jeu)."""

from enum import Enum, auto


class Phase(Enum):
    """Phase courante du tour.

    Les transitions exactes entre phases relèvent des features de boucle de tour ;
    ce type sert à l'inspection et à la cohérence avec :class:`Step`.
    """

    BEGINNING = auto()
    PRECOMBAT_MAIN = auto()
    COMBAT = auto()
    POSTCOMBAT_MAIN = auto()
    ENDING = auto()
