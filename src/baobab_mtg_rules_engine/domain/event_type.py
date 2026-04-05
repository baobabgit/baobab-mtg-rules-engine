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
    TURN_STEP_ENTERED = auto()
    TURN_STEP_ADVANCED = auto()
    TURN_ROLLED_TO_NEXT_PLAYER = auto()
    PRIORITY_ASSIGNED = auto()
    PRIORITY_PASSED = auto()
    TURN_DRAW_PERFORMED = auto()
    TURN_DRAW_STEP_SKIPPED_FIRST_DUEL_TURN = auto()
    FLOATING_MANA_CLEARED = auto()
    LAND_PLAYED = auto()
    SPELL_CAST = auto()
    SIMPLE_ABILITY_ACTIVATED = auto()
    ATTACKER_DECLARED = auto()
    BLOCKER_DECLARED = auto()
