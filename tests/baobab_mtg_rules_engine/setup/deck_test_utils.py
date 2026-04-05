"""Utilitaires de construction de decks pour les tests de setup."""

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.setup.deck_definition import DeckDefinition
from baobab_mtg_rules_engine.setup.game_factory import GameFactory


def make_sixty_card_deck(*, name: str = "deck", prefix: str = "c") -> DeckDefinition:
    """Construit un deck légal 60 cartes (15 clés × 4)."""
    entries = tuple((f"{prefix}{i}", 4) for i in range(15))
    return DeckDefinition(name, entries)


def make_catalog_two_prefixes() -> InMemoryCardCatalogAdapter:
    """Catalogue couvrant ``c0``–``c14`` et ``d0``–``d14``."""
    keys = frozenset(f"c{i}" for i in range(15)) | frozenset(f"d{i}" for i in range(15))
    return InMemoryCardCatalogAdapter(keys)


def make_game_factory_with_two_standard_decks() -> (
    tuple[GameFactory, tuple[DeckDefinition, DeckDefinition]]
):
    """Usine et paire de decks 60 cartes (préfixes ``c`` / ``d``) pour scénarios 1v1."""
    catalog = make_catalog_two_prefixes()
    factory = GameFactory(catalog)
    decks = (make_sixty_card_deck(prefix="c"), make_sixty_card_deck(prefix="d"))
    return factory, decks
