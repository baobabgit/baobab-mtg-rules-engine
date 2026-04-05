"""Tests pour :class:`DeckDefinition`."""

import pytest

from baobab_mtg_rules_engine.setup.deck_definition import DeckDefinition


class TestDeckDefinition:
    """Validation structurelle et expansion déterministe."""

    def test_total_cards(self) -> None:
        """:meth:`total_cards` agrège les quantités."""
        deck = DeckDefinition("x", (("a", 3), ("b", 2)))
        assert deck.total_cards() == 5

    def test_sorted_expansion_order(self) -> None:
        """L'expansion trie les clés pour le déterminisme avant mélange."""
        deck = DeckDefinition("x", (("z", 1), ("a", 2)))
        assert deck.sorted_expansion_keys() == ("a", "a", "z")

    def test_rejects_empty_name(self) -> None:
        """Un nom vide est refusé."""
        with pytest.raises(ValueError, match="nom"):
            DeckDefinition("", (("a", 1),))

    def test_rejects_non_positive_qty(self) -> None:
        """Les quantités nulles ou négatives sont refusées."""
        with pytest.raises(ValueError, match="Quantité"):
            DeckDefinition("x", (("a", 0),))

    def test_rejects_blank_catalog_key(self) -> None:
        """Une clé catalogue vide ou blanche est refusée."""
        with pytest.raises(ValueError, match="clés catalogue"):
            DeckDefinition("x", (("  ", 1),))
