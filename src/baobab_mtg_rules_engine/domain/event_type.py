"""Types d'événements enregistrés dans l'historique minimal de partie."""

from enum import Enum, auto


class EventType(Enum):
    """Catégorie d'événement pour le journal déterministe de :class:`GameState`."""

    GAME_INITIALIZED = auto()
    OBJECT_REGISTERED = auto()
    OBJECT_RELOCATED = auto()
    OBJECT_REPLACED_BY_NEW_IDENTITY = auto()
