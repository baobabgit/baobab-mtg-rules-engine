"""Adaptateur optionnel vers le paquet ``baobab-mtg-catalog`` (si installé)."""

from __future__ import annotations

import importlib
from typing import Any

from baobab_mtg_rules_engine.catalog.card_definition_port import CardDefinitionPort
from baobab_mtg_rules_engine.exceptions.unsupported_rule_exception import UnsupportedRuleException


class BaobabMtgCatalogAdapter(CardDefinitionPort):
    """Pont vers ``baobab-mtg-catalog`` lorsque l'API attendue est disponible.

    Si le module est absent ou n'expose pas ``is_supported_catalog_key`` et
    ``allows_unlimited_copies`` comme callables sur le module racine, une erreur
    explicite est levée : utilisez :class:`InMemoryCardCatalogAdapter` pour les tests.

    L'instance conserve une référence au module chargé pour les appels dynamiques.
    """

    def __init__(self) -> None:
        try:
            catalog_module: Any = importlib.import_module("baobab_mtg_catalog")
        except ImportError as exc:
            msg = (
                "Le paquet baobab-mtg-catalog est requis pour BaobabMtgCatalogAdapter. "
                "Installez-le ou utilisez InMemoryCardCatalogAdapter."
            )
            raise UnsupportedRuleException(msg, rule_reference="setup-catalog") from exc
        self._catalog: Any = catalog_module
        if not (
            callable(getattr(self._catalog, "is_supported_catalog_key", None))
            and callable(getattr(self._catalog, "allows_unlimited_copies", None))
        ):
            msg = (
                "baobab_mtg_catalog doit exposer is_supported_catalog_key et "
                "allows_unlimited_copies (callables). Sinon utilisez InMemoryCardCatalogAdapter."
            )
            raise UnsupportedRuleException(msg, rule_reference="setup-catalog-api")

    def is_supported_catalog_key(self, catalog_key: str) -> bool:
        """:return: Délégation au catalogue Baobab."""
        fn = self._catalog.is_supported_catalog_key
        return bool(fn(catalog_key))

    def allows_unlimited_copies(self, catalog_key: str) -> bool:
        """:return: Délégation au catalogue Baobab."""
        fn = self._catalog.allows_unlimited_copies
        return bool(fn(catalog_key))
