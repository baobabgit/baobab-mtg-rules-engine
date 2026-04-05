"""Référence de carte côté catalogue (sans couplage au catalogue Baobab)."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CardReference:
    """Référence stable vers une carte dans un catalogue externe.

    Le moteur ne résout pas cette clé : elle matérialise uniquement la distinction
    entre *référence de carte* et *objet en partie* (:class:`InGameCard` et dérivés).

    :param catalog_key: Clé opaque (ex. identifiant oracle, tuple sérialisé, etc.).
    """

    catalog_key: str

    def __post_init__(self) -> None:
        if not self.catalog_key:
            msg = "catalog_key ne doit pas être vide."
            raise ValueError(msg)
