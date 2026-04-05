"""Point d'extension structurel pour les capacités (hors implémentation)."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class AbilityLike(Protocol):
    """Contrat minimal pour brancher ultérieurement l'exécution de capacités.

    Ce protocole ne transporte aucune logique de jeu : il sert uniquement de
    point d'ancrage typé pour des extensions futures.
    """

    @property
    def ability_key(self) -> str:
        """Clé stable permettant d'identifier la capacité côté moteur ou plugins.

        :return: Identifiant logique non vide.
        """
