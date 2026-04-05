"""Action de jeu refusée après validation de légalité."""

from baobab_mtg_rules_engine.exceptions.validation_exception import ValidationException


class IllegalGameActionError(ValidationException):
    """Une action demandée viole le timing, la zone, la priorité ou les coûts supportés."""
