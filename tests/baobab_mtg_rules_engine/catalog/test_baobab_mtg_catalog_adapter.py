"""Tests pour :class:`BaobabMtgCatalogAdapter`."""

from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import pytest

from baobab_mtg_rules_engine.catalog.baobab_mtg_catalog_adapter import BaobabMtgCatalogAdapter
from baobab_mtg_rules_engine.exceptions.unsupported_rule_exception import UnsupportedRuleException


class TestBaobabMtgCatalogAdapter:
    """Chargement dynamique et refus explicite si l'API catalogue manque."""

    def test_import_error_raises_unsupported_rule(self) -> None:
        """Sans paquet installé, l'adaptateur refuse avec une cause claire."""
        with patch(
            "baobab_mtg_rules_engine.catalog.baobab_mtg_catalog_adapter.importlib.import_module",
            side_effect=ImportError("no catalog"),
        ):
            with pytest.raises(UnsupportedRuleException, match="baobab-mtg-catalog"):
                BaobabMtgCatalogAdapter()

    def test_module_without_api_raises(self) -> None:
        """Un module sans les callables attendus est refusé."""
        fake = ModuleType("baobab_mtg_catalog")
        with patch(
            "baobab_mtg_rules_engine.catalog.baobab_mtg_catalog_adapter.importlib.import_module",
            return_value=fake,
        ):
            with pytest.raises(UnsupportedRuleException, match="is_supported_catalog_key"):
                BaobabMtgCatalogAdapter()

    def test_delegates_to_module_functions(self) -> None:
        """Les méthodes délèguent au module chargé."""

        def is_supported_catalog_key(key: str) -> bool:
            return key == "k1"

        def allows_unlimited_copies(_key: str) -> bool:
            return False

        fake = SimpleNamespace(
            is_supported_catalog_key=is_supported_catalog_key,
            allows_unlimited_copies=allows_unlimited_copies,
        )
        with patch(
            "baobab_mtg_rules_engine.catalog.baobab_mtg_catalog_adapter.importlib.import_module",
            return_value=fake,
        ):
            adapter = BaobabMtgCatalogAdapter()
        assert adapter.is_supported_catalog_key("k1") is True
        assert adapter.is_supported_catalog_key("x") is False
        assert adapter.allows_unlimited_copies("k1") is False
