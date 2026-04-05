"""Types d'événements enregistrés dans l'historique minimal de partie."""

from enum import Enum, auto


class EventType(Enum):
    """Catégorie d'événement pour le journal déterministe de :class:`GameState`."""

    GAME_INITIALIZED = auto()
    OBJECT_REGISTERED = auto()
    OBJECT_RELOCATED = auto()
    OBJECT_REPLACED_BY_NEW_IDENTITY = auto()
    SETUP_DECKS_VALIDATED = auto()
    SETUP_LIBRARY_BUILT = auto()
    SETUP_LIBRARY_SHUFFLED = auto()
    SETUP_STARTING_PLAYER_DETERMINED = auto()
    SETUP_OPENING_HAND_DRAWN = auto()
    SETUP_MULLIGAN_TAKEN = auto()
    SETUP_FIRST_TURN_READY = auto()
