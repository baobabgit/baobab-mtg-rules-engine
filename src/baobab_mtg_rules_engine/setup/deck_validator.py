"""Validation des decks construits contre un :class:`CardDefinitionPort`."""

from baobab_mtg_rules_engine.catalog.card_definition_port import CardDefinitionPort
from baobab_mtg_rules_engine.exceptions.deck_validation_error import DeckValidationError
from baobab_mtg_rules_engine.setup.deck_definition import DeckDefinition


class DeckValidator:
    """Règles minimales pour une partie construite 1v1 (hors Commander).

    - Entre ``60`` et ``250`` cartes.
    - Chaque clé doit être supportée par le catalogue.
    - Au plus ``4`` exemplaires d'une même clé sauf si ``allows_unlimited_copies``.

    :param catalog: Port catalogue utilisé pour les vérifications.
    """

    MIN_MAIN_DECK_SIZE: int = 60
    MAX_MAIN_DECK_SIZE: int = 250
    MAX_COPY_NON_UNLIMITED: int = 4

    def __init__(self, catalog: CardDefinitionPort) -> None:
        self._catalog: CardDefinitionPort = catalog

    def validate(self, deck: DeckDefinition) -> None:
        """Valide un deck principal avant toute mutation d'état.

        :param deck: Deck à contrôler.
        :raises DeckValidationError: si une contrainte est violée.
        """
        total = deck.total_cards()
        if total < self.MIN_MAIN_DECK_SIZE:
            msg = f"Deck trop petit ({total} cartes, minimum {self.MIN_MAIN_DECK_SIZE})."
            raise DeckValidationError(msg, field_name="deck")
        if total > self.MAX_MAIN_DECK_SIZE:
            msg = f"Deck trop volumineux ({total} cartes, maximum {self.MAX_MAIN_DECK_SIZE})."
            raise DeckValidationError(msg, field_name="deck")
        counts: dict[str, int] = {}
        for catalog_key, qty in deck.entries:
            if not self._catalog.is_supported_catalog_key(catalog_key):
                msg = f"Clé catalogue non supportée : {catalog_key!r}."
                raise DeckValidationError(msg, field_name="catalog_key")
            counts[catalog_key] = counts.get(catalog_key, 0) + qty
        for catalog_key, qty in counts.items():
            if self._catalog.allows_unlimited_copies(catalog_key):
                continue
            if qty > self.MAX_COPY_NON_UNLIMITED:
                msg = (
                    f"Trop d'exemplaires pour {catalog_key!r} "
                    f"({qty} > {self.MAX_COPY_NON_UNLIMITED})."
                )
                raise DeckValidationError(msg, field_name="deck")
