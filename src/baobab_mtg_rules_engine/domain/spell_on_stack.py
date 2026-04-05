"""Sort (ou copie de sort) sur la pile."""

from baobab_mtg_rules_engine.domain.in_game_card import InGameCard


class SpellOnStack(InGameCard):
    """Objet de sort présent sur la pile.

    Hérite du constructeur :class:`InGameCard`.
    """

    @property
    def kind_label(self) -> str:
        """:return: Libellé de catégorie."""
        return "spell_on_stack"
