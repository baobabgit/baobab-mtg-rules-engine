"""Capacité déclenchée ou activée modélisée comme objet sur la pile."""

from baobab_mtg_rules_engine.domain.game_object import GameObject
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


class AbilityOnStack(GameObject):
    """Capacité sur la pile, liée optionnellement à un objet source.

    :param object_id: Identifiant d'objet dans la partie.
    :param source_object_id: Objet dont la capacité provient, si applicable.
    :param ability_key: Clé logique de la capacité (extension future).
    """

    def __init__(
        self,
        object_id: GameObjectId,
        *,
        source_object_id: GameObjectId | None = None,
        ability_key: str = "generic",
    ) -> None:
        super().__init__(object_id)
        self._source_object_id: GameObjectId | None = source_object_id
        self._ability_key: str = ability_key

    @property
    def source_object_id(self) -> GameObjectId | None:
        """:return: Identifiant de l'objet source ou ``None``."""
        return self._source_object_id

    @property
    def ability_key(self) -> str:
        """:return: Clé de capacité."""
        return self._ability_key

    @property
    def kind_label(self) -> str:
        """:return: Libellé de catégorie."""
        return "ability_on_stack"
