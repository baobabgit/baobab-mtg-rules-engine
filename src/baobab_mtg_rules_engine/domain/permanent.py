"""Permanent sur le champ de bataille."""

from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError


class Permanent(InGameCard):
    """Permanent : carte ou représentation carte sur le champ de bataille.

    Hérite du constructeur :class:`InGameCard` (``object_id``, ``card_reference``).
    Les blessures marquées servent au combat simplifié et aux ABS.

    :param marked_damage: Dégâts marqués sur la créature (non négatifs).
    """

    def __init__(
        self,
        object_id: GameObjectId,
        card_reference: CardReference,
        *,
        marked_damage: int = 0,
    ) -> None:
        super().__init__(object_id, card_reference)
        if marked_damage < 0:
            msg = "Les blessures marquées ne peuvent pas être négatives."
            raise InvalidGameStateError(msg, field_name="marked_damage")
        self._marked_damage: int = marked_damage

    @property
    def kind_label(self) -> str:
        """:return: Libellé de catégorie."""
        return "permanent"

    @property
    def marked_damage(self) -> int:
        """:return: Total des dégâts marqués sur ce permanent."""
        return self._marked_damage

    def add_marked_damage(self, amount: int) -> None:
        """Ajoute des dégâts marqués (combat ou effet direct minimal).

        :param amount: Strictement positif.
        :raises InvalidGameStateError: si ``amount`` invalide.
        """
        if amount < 1:
            msg = "Le montant de dégâts marqués doit être au moins 1."
            raise InvalidGameStateError(msg, field_name="amount")
        self._marked_damage += amount

    def clear_marked_damage(self) -> None:
        """Remet les blessures marquées à zéro (ex. fin de tour simplifiée)."""
        self._marked_damage = 0
