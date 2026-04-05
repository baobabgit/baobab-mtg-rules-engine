"""Erreur levée lorsque l'état de partie ou une opération de domaine est invalide."""

from baobab_mtg_rules_engine.exceptions.validation_exception import ValidationException


class InvalidGameStateError(ValidationException):
    """Violation d'invariant du domaine « partie / état ».

    Utilisée pour les constructions ou mutations incohérentes avant toute logique
    de règles complète (périmètre de la feature domaine).
    """
