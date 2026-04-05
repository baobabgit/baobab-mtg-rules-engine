"""Erreur lorsqu'une pioche demandée dépasse la taille de la bibliothèque."""

from baobab_mtg_rules_engine.exceptions.validation_exception import ValidationException


class InsufficientLibraryError(ValidationException):
    """La bibliothèque ne contient pas assez de cartes pour la pioche.

    Utilisée pendant le setup ou toute phase où une défaite par pioche
    ne doit pas être inférée implicitement.
    """
