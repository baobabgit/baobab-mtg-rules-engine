"""Cible de sort invalide au lancement ou incohérente avec le catalogue."""

from baobab_mtg_rules_engine.exceptions.validation_exception import ValidationException


class InvalidSpellTargetError(ValidationException):
    """Les cibles fournies violent les contraintes du port gameplay ou de la zone."""
