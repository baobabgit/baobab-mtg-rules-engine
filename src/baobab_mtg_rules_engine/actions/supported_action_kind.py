"""Catalogue des familles d'actions reconnues par le moteur légal (ordre de tri)."""

from enum import Enum, auto


class SupportedActionKind(Enum):
    """Identifiant stable pour tri déterministe des actions légales."""

    PASS_PRIORITY = auto()
    PLAY_LAND = auto()
    CAST_SPELL = auto()
    ACTIVATE_SIMPLE_ABILITY = auto()
    DECLARE_ATTACKER = auto()
    DECLARE_BLOCKER = auto()
