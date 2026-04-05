"""Tests pour :class:`AbilityOnStack` et le protocole :class:`AbilityLike`."""

from baobab_mtg_rules_engine.domain.ability_like import AbilityLike
from baobab_mtg_rules_engine.domain.ability_on_stack import AbilityOnStack
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


class TestAbilityOnStack:
    """Capacité sur la pile et point d'extension."""

    def test_kind_label_and_source(self) -> None:
        """Métadonnées de base pour inspection."""
        src = GameObjectId(2)
        ability = AbilityOnStack(GameObjectId(1), source_object_id=src, ability_key="activated")
        assert ability.kind_label == "ability_on_stack"
        assert ability.source_object_id == src
        assert ability.ability_key == "activated"

    def test_satisfies_ability_like_protocol(self) -> None:
        """L'objet peut être traité comme :class:`AbilityLike` (runtime)."""
        ability = AbilityOnStack(GameObjectId(3))
        assert isinstance(ability, AbilityLike)
