"""Adaptateur optionnel vers le paquet ``baobab-mtg-catalog`` (si installé)."""

from __future__ import annotations

import importlib
from typing import Any

from baobab_mtg_rules_engine.catalog.card_definition_port import CardDefinitionPort
from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.domain.triggered_ability_definition import TriggeredAbilityDefinition
from baobab_mtg_rules_engine.exceptions.unsupported_rule_exception import UnsupportedRuleException


class BaobabMtgCatalogAdapter(CardDefinitionPort, CardGameplayPort):
    """Pont vers ``baobab-mtg-catalog`` lorsque l'API attendue est disponible.

    Si le module est absent ou n'expose pas ``is_supported_catalog_key`` et
    ``allows_unlimited_copies`` comme callables sur le module racine, une erreur
    explicite est levée : utilisez :class:`InMemoryCardCatalogAdapter` pour les tests.

    L'instance conserve une référence au module chargé pour les appels dynamiques.
    """

    def __init__(self) -> None:
        try:
            catalog_module: Any = importlib.import_module("baobab_mtg_catalog")
        except ImportError as exc:
            msg = (
                "Le paquet baobab-mtg-catalog est requis pour BaobabMtgCatalogAdapter. "
                "Installez-le ou utilisez InMemoryCardCatalogAdapter."
            )
            raise UnsupportedRuleException(msg, rule_reference="setup-catalog") from exc
        self._catalog: Any = catalog_module
        if not (
            callable(getattr(self._catalog, "is_supported_catalog_key", None))
            and callable(getattr(self._catalog, "allows_unlimited_copies", None))
        ):
            msg = (
                "baobab_mtg_catalog doit exposer is_supported_catalog_key et "
                "allows_unlimited_copies (callables). Sinon utilisez InMemoryCardCatalogAdapter."
            )
            raise UnsupportedRuleException(msg, rule_reference="setup-catalog-api")

    def is_supported_catalog_key(self, catalog_key: str) -> bool:
        """:return: Délégation au catalogue Baobab."""
        fn = self._catalog.is_supported_catalog_key
        return bool(fn(catalog_key))

    def allows_unlimited_copies(self, catalog_key: str) -> bool:
        """:return: Délégation au catalogue Baobab."""
        fn = self._catalog.allows_unlimited_copies
        return bool(fn(catalog_key))

    def is_land_catalog_key(self, catalog_key: str) -> bool:
        """:raises UnsupportedRuleException: métadonnées de jeu non branchées sur ce catalogue."""
        _ = catalog_key
        msg = "Les métadonnées CardGameplayPort ne sont pas encore exposées par baobab-mtg-catalog."
        raise UnsupportedRuleException(msg, rule_reference="catalog-gameplay")

    def is_creature_catalog_key(self, catalog_key: str) -> bool:
        _ = catalog_key
        msg = "Les métadonnées CardGameplayPort ne sont pas encore exposées par baobab-mtg-catalog."
        raise UnsupportedRuleException(msg, rule_reference="catalog-gameplay")

    def is_sorcery_speed_spell_catalog_key(self, catalog_key: str) -> bool:
        _ = catalog_key
        msg = "Les métadonnées CardGameplayPort ne sont pas encore exposées par baobab-mtg-catalog."
        raise UnsupportedRuleException(msg, rule_reference="catalog-gameplay")

    def is_instant_speed_spell_catalog_key(self, catalog_key: str) -> bool:
        _ = catalog_key
        msg = "Les métadonnées CardGameplayPort ne sont pas encore exposées par baobab-mtg-catalog."
        raise UnsupportedRuleException(msg, rule_reference="catalog-gameplay")

    def spell_generic_mana_cost(self, catalog_key: str) -> int:
        _ = catalog_key
        msg = "Les métadonnées CardGameplayPort ne sont pas encore exposées par baobab-mtg-catalog."
        raise UnsupportedRuleException(msg, rule_reference="catalog-gameplay")

    def spell_target_kind(self, catalog_key: str) -> str:
        _ = catalog_key
        msg = "Les métadonnées CardGameplayPort ne sont pas encore exposées par baobab-mtg-catalog."
        raise UnsupportedRuleException(msg, rule_reference="catalog-gameplay")

    def is_creature_spell_catalog_key(self, catalog_key: str) -> bool:
        _ = catalog_key
        msg = "Les métadonnées CardGameplayPort ne sont pas encore exposées par baobab-mtg-catalog."
        raise UnsupportedRuleException(msg, rule_reference="catalog-gameplay")

    def spell_damage_to_player_amount(self, catalog_key: str) -> int:
        _ = catalog_key
        msg = "Les métadonnées CardGameplayPort ne sont pas encore exposées par baobab-mtg-catalog."
        raise UnsupportedRuleException(msg, rule_reference="catalog-gameplay")

    def simple_activated_ability_costs(self, catalog_key: str) -> tuple[int, ...]:
        _ = catalog_key
        msg = "Les métadonnées CardGameplayPort ne sont pas encore exposées par baobab-mtg-catalog."
        raise UnsupportedRuleException(msg, rule_reference="catalog-gameplay")

    def creature_power(self, catalog_key: str) -> int:
        _ = catalog_key
        msg = "Les métadonnées CardGameplayPort ne sont pas encore exposées par baobab-mtg-catalog."
        raise UnsupportedRuleException(msg, rule_reference="catalog-gameplay")

    def creature_toughness(self, catalog_key: str) -> int:
        _ = catalog_key
        msg = "Les métadonnées CardGameplayPort ne sont pas encore exposées par baobab-mtg-catalog."
        raise UnsupportedRuleException(msg, rule_reference="catalog-gameplay")

    def triggered_ability_definitions(
        self,
        catalog_key: str,
    ) -> tuple[TriggeredAbilityDefinition, ...]:
        _ = catalog_key
        msg = "Les métadonnées CardGameplayPort ne sont pas encore exposées par baobab-mtg-catalog."
        raise UnsupportedRuleException(msg, rule_reference="catalog-gameplay")
