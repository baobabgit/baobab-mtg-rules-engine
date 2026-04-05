"""Erreur lorsque la composition d'un deck viole les contraintes supportées."""

from baobab_mtg_rules_engine.exceptions.validation_exception import ValidationException


class DeckValidationError(ValidationException):
    """Deck illégal pour le format et le catalogue configurés."""
