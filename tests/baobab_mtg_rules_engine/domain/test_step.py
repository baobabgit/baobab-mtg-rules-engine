"""Tests pour :class:`Step` et le lien avec :class:`Phase`."""

import pytest

from baobab_mtg_rules_engine.domain.phase import Phase
from baobab_mtg_rules_engine.domain.step import Step


class TestStep:
    """Couverture du mapping étape → phase."""

    @pytest.mark.parametrize(
        ("step", "expected_phase"),
        [
            (Step.UNTAP, Phase.BEGINNING),
            (Step.UPKEEP, Phase.BEGINNING),
            (Step.DRAW, Phase.BEGINNING),
            (Step.MAIN_PRECOMBAT, Phase.PRECOMBAT_MAIN),
            (Step.BEGIN_COMBAT, Phase.COMBAT),
            (Step.DECLARE_ATTACKERS, Phase.COMBAT),
            (Step.DECLARE_BLOCKERS, Phase.COMBAT),
            (Step.COMBAT_DAMAGE, Phase.COMBAT),
            (Step.END_COMBAT, Phase.COMBAT),
            (Step.MAIN_POSTCOMBAT, Phase.POSTCOMBAT_MAIN),
            (Step.END_TURN, Phase.ENDING),
            (Step.CLEANUP, Phase.ENDING),
        ],
    )
    def test_phase_mapping(self, step: Step, expected_phase: Phase) -> None:
        """Chaque étape connue renvoie la phase MTG attendue."""
        assert step.phase() is expected_phase
