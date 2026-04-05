"""Contrat de deck principal (hors sideboard complet, hors Commander)."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeckDefinition:
    """Description immuable d'un deck construit pour le setup standard 1v1.

    Les entrées sont des paires ``(clé_catalogue, quantité)``. L'ordre logique
    de construction des cartes en bibliothèque avant mélange est dérivé en
    triant les clés pour le déterminisme.

    :param name: Nom d'inspection du deck.
    :param entries: Cartes et quantités ; quantités strictement positives.
    """

    name: str
    entries: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            msg = "Le nom du deck ne doit pas être vide."
            raise ValueError(msg)
        for key, qty in self.entries:
            if qty < 1:
                msg = f"Quantité invalide pour la clé {key!r}."
                raise ValueError(msg)
            if not key.strip():
                msg = "Les clés catalogue ne doivent pas être vides."
                raise ValueError(msg)

    def total_cards(self) -> int:
        """:return: Nombre total de cartes dans le deck principal."""
        return sum(qty for _, qty in self.entries)

    def sorted_expansion_keys(self) -> tuple[str, ...]:
        """Déplie les entrées en liste de clés triées (multiplicité incluse).

        :return: Tuple déterministe de clés avant mélange.
        """
        keys: list[str] = []
        for catalog_key, qty in sorted(self.entries, key=lambda item: item[0]):
            keys.extend([catalog_key] * qty)
        return tuple(keys)
