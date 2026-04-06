"""Erreur de séquence de replay ou d'instruction d'enregistrement."""

from baobab_mtg_rules_engine.exceptions.validation_exception import ValidationException


class ReplaySequenceError(ValidationException):
    """Levée lorsqu'une instruction de replay est invalide, incomplète ou non supportée."""
