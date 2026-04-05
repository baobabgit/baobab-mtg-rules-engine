"""Adaptateur catalogue en mémoire pour tests et environnements sans dépendance distante."""

from baobab_mtg_rules_engine.catalog.card_definition_port import CardDefinitionPort
from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort


class InMemoryCardCatalogAdapter(CardDefinitionPort, CardGameplayPort):
    """Catalogue minimal : decks, types de carte et coûts pour le moteur légal."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        supported_keys: frozenset[str],
        *,
        unlimited_copy_keys: frozenset[str] | None = None,
        land_keys: frozenset[str] | None = None,
        creature_keys: frozenset[str] | None = None,
        sorcery_spell_keys: frozenset[str] | None = None,
        instant_spell_keys: frozenset[str] | None = None,
        spell_mana_cost_by_key: dict[str, int] | None = None,
        activated_ability_costs_by_key: dict[str, tuple[int, ...]] | None = None,
    ) -> None:
        self._supported: frozenset[str] = supported_keys
        self._unlimited: frozenset[str] = unlimited_copy_keys or frozenset()
        self._lands: frozenset[str] = land_keys or frozenset()
        self._creatures: frozenset[str] = creature_keys or frozenset()
        self._sorcery_spells: frozenset[str] = sorcery_spell_keys or frozenset()
        self._instant_spells: frozenset[str] = instant_spell_keys or frozenset()
        self._spell_costs: dict[str, int] = dict(spell_mana_cost_by_key or {})
        self._activated_costs: dict[str, tuple[int, ...]] = dict(
            activated_ability_costs_by_key or {},
        )

    def is_supported_catalog_key(self, catalog_key: str) -> bool:
        """:return: Appartenance à l'ensemble supporté."""
        return catalog_key in self._supported

    def allows_unlimited_copies(self, catalog_key: str) -> bool:
        """:return: ``True`` pour les clés déclarées « terrains de base » ou équivalent."""
        return catalog_key in self._unlimited

    def is_land_catalog_key(self, catalog_key: str) -> bool:
        """:return: Terrain jouable."""
        return catalog_key in self._lands

    def is_creature_catalog_key(self, catalog_key: str) -> bool:
        """:return: Créature."""
        return catalog_key in self._creatures

    def is_sorcery_speed_spell_catalog_key(self, catalog_key: str) -> bool:
        """:return: Sort à vitesse rituelle."""
        return catalog_key in self._sorcery_spells

    def is_instant_speed_spell_catalog_key(self, catalog_key: str) -> bool:
        """:return: Sort à vitesse instantanée."""
        return catalog_key in self._instant_spells

    def spell_generic_mana_cost(self, catalog_key: str) -> int:
        """:return: Coût générique ou ``0``."""
        return int(self._spell_costs.get(catalog_key, 0))

    def simple_activated_ability_costs(self, catalog_key: str) -> tuple[int, ...]:
        """:return: Coûts d'activation simples enregistrés."""
        return tuple(self._activated_costs.get(catalog_key, ()))
