"""Tests pour :class:`InMemoryCardCatalogAdapter`."""

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)


class TestInMemoryCardCatalogAdapter:
    """Ensembles de clés supportées et copies illimitées optionnelles."""

    def test_supported_and_unsupported_keys(self) -> None:
        """Seules les clés déclarées sont reconnues."""
        adapter = InMemoryCardCatalogAdapter(frozenset({"a", "b"}))
        assert adapter.is_supported_catalog_key("a") is True
        assert adapter.is_supported_catalog_key("z") is False

    def test_unlimited_subset(self) -> None:
        """Les clés « illimitées » sont distinguées du simple support."""
        adapter = InMemoryCardCatalogAdapter(
            frozenset({"land", "spell"}),
            unlimited_copy_keys=frozenset({"land"}),
        )
        assert adapter.allows_unlimited_copies("land") is True
        assert adapter.allows_unlimited_copies("spell") is False
