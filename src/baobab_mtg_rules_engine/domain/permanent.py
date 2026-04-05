"""Permanent sur le champ de bataille."""

from baobab_mtg_rules_engine.domain.in_game_card import InGameCard


class Permanent(InGameCard):
    """Permanent : carte ou représentation carte sur le champ de bataille.

    Hérite du constructeur :class:`InGameCard` (``object_id``, ``card_reference``).
    """

    @property
    def kind_label(self) -> str:
        """:return: Libellé de catégorie."""
        return "permanent"
