"""Point d'extension structurel pour les effets (hors implémentation)."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EffectLike(Protocol):
    """Contrat minimal pour brancher ultérieurement la résolution d'effets.

    Aucun effet n'est exécuté à ce stade : seul un identifiant logique est requis.
    """

    @property
    def effect_key(self) -> str:
        """Clé stable d'effet pour routage ou journalisation future.

        :return: Identifiant logique non vide.
        """
