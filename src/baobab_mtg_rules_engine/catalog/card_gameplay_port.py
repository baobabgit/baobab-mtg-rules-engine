"""Métadonnées de jeu par clé catalogue (timing, types, coûts génériques)."""

# Les corps ``...`` sont requis par :class:`typing.Protocol`.
# pylint: disable=unnecessary-ellipsis

from typing import Protocol, runtime_checkable


@runtime_checkable
class CardGameplayPort(Protocol):
    """Données minimales pour le calcul d'actions légales hors moteur de cartes complet.

    Les implémentations renvoient des booléens et coûts entiers génériques ; tout
    comportement non modélisé doit être refusé explicitement par l'adaptateur.
    """

    def is_land_catalog_key(self, catalog_key: str) -> bool:
        """:return: ``True`` si la clé désigne un terrain jouable comme terrain."""
        ...

    def is_creature_catalog_key(self, catalog_key: str) -> bool:
        """:return: ``True`` si la clé désigne une créature sur le champ de bataille."""
        ...

    def is_sorcery_speed_spell_catalog_key(self, catalog_key: str) -> bool:
        """:return: ``True`` si le sort suit le timing rituel (principales, pile vide, etc.)."""
        ...

    def is_instant_speed_spell_catalog_key(self, catalog_key: str) -> bool:
        """:return: ``True`` si le sort peut être lancé avec priorité (timing éphémère)."""
        ...

    def spell_generic_mana_cost(self, catalog_key: str) -> int:
        """:return: Coût mana générique entier ; ``0`` si la clé n'est pas un sort connu."""
        ...

    def simple_activated_ability_costs(self, catalog_key: str) -> tuple[int, ...]:
        """:return: Coûts mana génériques pour capacités activées simples ; vide si aucune."""
        ...
