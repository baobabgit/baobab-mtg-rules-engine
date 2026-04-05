"""Adaptateur catalogue en mémoire pour tests et environnements sans dépendance distante."""

from baobab_mtg_rules_engine.catalog.card_definition_port import CardDefinitionPort


class InMemoryCardCatalogAdapter(CardDefinitionPort):
    """Catalogue minimal basé sur des ensembles de clés autorisées.

    :param supported_keys: Clés reconnues comme cartes valides.
    :param unlimited_copy_keys: Sous-ensemble autorisé au-delà de quatre copies.
    """

    def __init__(
        self,
        supported_keys: frozenset[str],
        *,
        unlimited_copy_keys: frozenset[str] | None = None,
    ) -> None:
        self._supported: frozenset[str] = supported_keys
        self._unlimited: frozenset[str] = unlimited_copy_keys or frozenset()

    def is_supported_catalog_key(self, catalog_key: str) -> bool:
        """:return: Appartenance à l'ensemble supporté."""
        return catalog_key in self._supported

    def allows_unlimited_copies(self, catalog_key: str) -> bool:
        """:return: ``True`` pour les clés déclarées « terrains de base » ou équivalent."""
        return catalog_key in self._unlimited
