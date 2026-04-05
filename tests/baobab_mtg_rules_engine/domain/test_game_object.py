"""Tests pour :class:`GameObject` via sous-classe concrète."""

from baobab_mtg_rules_engine.domain.game_object import GameObject
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


class _ConcreteObject(GameObject):
    """Implémentation minimale pour tests."""

    @property
    def kind_label(self) -> str:
        return "concrete_test"


class TestGameObject:
    """Accès à l'identifiant sur la racine abstraite."""

    def test_object_id_exposed(self) -> None:
        """L'identifiant fourni au constructeur est exposé."""
        oid = GameObjectId(7)
        obj = _ConcreteObject(oid)
        assert obj.object_id == oid
        assert obj.kind_label == "concrete_test"
