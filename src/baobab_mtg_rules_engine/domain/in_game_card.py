"""Carte comme objet de jeu (distincte de la simple :class:`CardReference`)."""

from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.game_object import GameObject
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


class InGameCard(GameObject):
    """Représentation d'une carte engagée dans une partie.

    Distingue explicitement la référence catalogue (:class:`CardReference`) de
    l'instance de jeu identifiée par :attr:`object_id`.

    :param object_id: Identifiant d'objet dans la partie.
    :param card_reference: Référence vers la définition de carte.
    """

    def __init__(self, object_id: GameObjectId, card_reference: CardReference) -> None:
        super().__init__(object_id)
        self._card_reference: CardReference = card_reference

    @property
    def card_reference(self) -> CardReference:
        """Référence de carte côté catalogue.

        :return: Clé de catalogue immuable.
        """
        return self._card_reference

    @property
    def kind_label(self) -> str:
        """:return: Libellé de catégorie pour cette hiérarchie."""
        return "in_game_card"
