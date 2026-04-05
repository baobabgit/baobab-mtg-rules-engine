"""Port d'accès aux définitions de cartes (découple le moteur du catalogue concret)."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class CardDefinitionPort(Protocol):
    """Contrat minimal pour valider les clés de deck contre un catalogue.

    Les implémentations peuvent s'appuyer sur ``baobab-mtg-catalog``, un cache
    mémoire de tests ou tout autre source stable.
    """

    def is_supported_catalog_key(self, catalog_key: str) -> bool:
        """Indique si la clé est connue du catalogue.

        :param catalog_key: Identifiant opaque (ex. oracle id).
        :return: ``True`` si la carte peut figurer dans un deck.
        """

    def allows_unlimited_copies(self, catalog_key: str) -> bool:
        """Indique si la règle des quatre exemplaires ne s'applique pas.

        Typiquement réservé aux terrains de base dans les formats construits.

        :param catalog_key: Clé catalogue.
        :return: ``True`` si le nombre de copies n'est pas plafonné à quatre.
        """
