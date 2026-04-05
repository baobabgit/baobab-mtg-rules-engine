"""Tests pour :class:`DeckValidator`."""

import pytest

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.exceptions.deck_validation_error import DeckValidationError
from baobab_mtg_rules_engine.setup.deck_definition import DeckDefinition
from baobab_mtg_rules_engine.setup.deck_validator import DeckValidator

from .deck_test_utils import make_sixty_card_deck


class TestDeckValidator:
    """Règles de taille, catalogue et exemplaires."""

    def test_accepts_valid_60(self) -> None:
        """Un deck 60 valide passe la validation."""
        catalog = InMemoryCardCatalogAdapter(frozenset(f"c{i}" for i in range(15)))
        deck = make_sixty_card_deck()
        DeckValidator(catalog).validate(deck)

    def test_rejects_unknown_key(self) -> None:
        """Une clé absente du catalogue est refusée."""
        catalog = InMemoryCardCatalogAdapter(
            frozenset({"only"}), unlimited_copy_keys=frozenset({"only"})
        )
        deck = DeckDefinition("bad", (("introuvable", 60),))
        with pytest.raises(DeckValidationError, match="non supportée"):
            DeckValidator(catalog).validate(deck)

    def test_rejects_too_small(self) -> None:
        """Moins de 60 cartes est refusé."""
        catalog = InMemoryCardCatalogAdapter(frozenset({"a"}), unlimited_copy_keys=frozenset({"a"}))
        deck = DeckDefinition("small", (("a", 59),))
        with pytest.raises(DeckValidationError, match="trop petit"):
            DeckValidator(catalog).validate(deck)

    def test_rejects_too_large(self) -> None:
        """Plus de 250 cartes est refusé."""
        catalog = InMemoryCardCatalogAdapter(frozenset({"a"}), unlimited_copy_keys=frozenset({"a"}))
        deck = DeckDefinition("big", (("a", 251),))
        with pytest.raises(DeckValidationError, match="trop volumineux"):
            DeckValidator(catalog).validate(deck)

    def test_rejects_fifth_copy(self) -> None:
        """Plus de quatre exemplaires non basiques est refusé."""
        catalog = InMemoryCardCatalogAdapter(
            frozenset({"spell", "land"}), unlimited_copy_keys=frozenset({"land"})
        )
        deck = DeckDefinition("x", (("spell", 5), ("land", 55)))
        with pytest.raises(DeckValidationError, match="Trop d'exemplaires"):
            DeckValidator(catalog).validate(deck)

    def test_allows_unlimited_copies_beyond_four(self) -> None:
        """Les clés « illimitées » peuvent dépasser quatre exemplaires."""
        catalog = InMemoryCardCatalogAdapter(
            frozenset({"mountain"}), unlimited_copy_keys=frozenset({"mountain"})
        )
        deck = DeckDefinition("mono", (("mountain", 60),))
        DeckValidator(catalog).validate(deck)
