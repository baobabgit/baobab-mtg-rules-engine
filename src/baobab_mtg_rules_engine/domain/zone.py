"""Zone ordonnée d'objets de jeu."""

from collections import Counter

from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.zone_type import ZoneType


class Zone:
    """Liste ordonnée d'identifiants d'objets appartenant à une zone donnée.

    :param zone_type: Type logique de la zone.
    :param owner_player_index: Propriétaire pour les zones joueur ; ``None`` pour la pile.
    """

    def __init__(self, zone_type: ZoneType, owner_player_index: int | None) -> None:
        self._zone_type: ZoneType = zone_type
        self._owner_player_index: int | None = owner_player_index
        self._order: list[GameObjectId] = []

    @property
    def zone_type(self) -> ZoneType:
        """:return: Type de zone."""
        return self._zone_type

    @property
    def owner_player_index(self) -> int | None:
        """:return: Index joueur propriétaire ou ``None``."""
        return self._owner_player_index

    def object_ids(self) -> tuple[GameObjectId, ...]:
        """Copie immuable de l'ordre courant.

        :return: Tuple des identifiants de la tête vers la queue.
        """
        return tuple(self._order)

    def contains(self, object_id: GameObjectId) -> bool:
        """:return: ``True`` si l'identifiant est présent dans la zone."""
        return object_id in self._order

    def append(self, object_id: GameObjectId) -> None:
        """Ajoute l'objet en fin de zone (ordre LIFO pour la pile, etc.).

        :param object_id: Identifiant à placer.
        """
        self._order.append(object_id)

    def remove(self, object_id: GameObjectId) -> None:
        """Retire la première occurrence de l'identifiant.

        :param object_id: Identifiant à retirer.
        :raises ValueError: si l'objet est absent.
        """
        self._order.remove(object_id)

    def replace_ordered_contents(self, new_order: tuple[GameObjectId, ...]) -> None:
        """Remplace l'ordre courant en conservant exactement le même multi-ensemble.

        Utilisé pour les mélanges déterministes de bibliothèque.

        :param new_order: Nouvelle permutation des identifiants déjà présents.
        :raises ValueError: si le multi-ensemble ne correspond pas à la zone actuelle.
        """
        if Counter(self._order) != Counter(new_order):
            msg = "replace_ordered_contents exige le même ensemble de cartes."
            raise ValueError(msg)
        self._order[:] = list(new_order)
