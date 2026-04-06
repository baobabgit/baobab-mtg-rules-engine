"""Tests pour :class:`AttackerDeclarationService`."""

import pytest

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.combat.attacker_declaration_service import AttackerDeclarationService
from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.illegal_game_action_error import IllegalGameActionError


class TestAttackerDeclarationService:
    """Contraintes minimales."""

    def test_zero_power_creature_rejected(self) -> None:
        """Sans force catalogue positive, pas d'attaque."""
        state = GameState.new_two_player()
        oid = state.issue_object_id()
        state.register_object_at(
            Permanent(oid, CardReference("wall")),
            ZoneLocation(0, ZoneType.BATTLEFIELD),
        )
        rules = InMemoryCardCatalogAdapter(
            frozenset({"wall"}),
            creature_keys=frozenset({"wall"}),
            creature_power_toughness_by_key={"wall": (0, 4)},
        )
        with pytest.raises(IllegalGameActionError, match="Force"):
            AttackerDeclarationService().validate_and_apply(
                state,
                rules,
                active_player_index=0,
                creature_object_id=oid,
            )
