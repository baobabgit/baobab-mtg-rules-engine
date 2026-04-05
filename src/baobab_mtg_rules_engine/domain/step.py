"""Étapes de tour et lien avec la :class:`Phase` correspondante."""

from enum import Enum, auto

from baobab_mtg_rules_engine.domain.phase import Phase


class Step(Enum):
    """Étape détaillée du tour.

    Le sous-ensemble d'étapes est volontairement compact pour le bootstrap du domaine.
    """

    UNTAP = auto()
    UPKEEP = auto()
    DRAW = auto()
    MAIN_PRECOMBAT = auto()
    BEGIN_COMBAT = auto()
    DECLARE_ATTACKERS = auto()
    DECLARE_BLOCKERS = auto()
    COMBAT_DAMAGE = auto()
    END_COMBAT = auto()
    MAIN_POSTCOMBAT = auto()
    END_TURN = auto()
    CLEANUP = auto()

    def phase(self) -> Phase:
        """Phase MTG associée à cette étape.

        :return: Phase contenant cette étape.
        """
        if self in (Step.UNTAP, Step.UPKEEP, Step.DRAW):
            return Phase.BEGINNING
        if self is Step.MAIN_PRECOMBAT:
            return Phase.PRECOMBAT_MAIN
        if self in (
            Step.BEGIN_COMBAT,
            Step.DECLARE_ATTACKERS,
            Step.DECLARE_BLOCKERS,
            Step.COMBAT_DAMAGE,
            Step.END_COMBAT,
        ):
            return Phase.COMBAT
        if self is Step.MAIN_POSTCOMBAT:
            return Phase.POSTCOMBAT_MAIN
        return Phase.ENDING
