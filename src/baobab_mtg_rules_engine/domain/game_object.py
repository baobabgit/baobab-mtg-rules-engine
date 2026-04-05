"""Objet de jeu abstrait porté par un :class:`GameObjectId`."""

from abc import ABC, abstractmethod

from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


class GameObject(ABC):
    """Racine des objets manipulés par le moteur dans une :class:`GameState`.

    :param object_id: Identifiant stable attribué par la partie.
    """

    def __init__(self, object_id: GameObjectId) -> None:
        self._object_id: GameObjectId = object_id

    @property
    def object_id(self) -> GameObjectId:
        """Identifiant technique de l'objet.

        :return: Identifiant immutable de la partie.
        """
        return self._object_id

    @property
    @abstractmethod
    def kind_label(self) -> str:
        """Libellé court pour inspection / événements (non destiné aux joueurs).

        :return: Nom de catégorie stable (ex. ``permanent``).
        """
