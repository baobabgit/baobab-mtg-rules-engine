"""Tests pour :class:`BlockerDeclarationService`."""

import pytest

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.combat.blocker_declaration_service import BlockerDeclarationService
from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.illegal_game_action_error import IllegalGameActionError


class TestBlockerDeclarationService:
    """Un bloqueur par attaquant."""

    def test_second_blocker_on_same_attacker_rejected(self) -> None:
        """Refus explicite si l'attaquant est déjà engagé."""
        state = GameState.new_two_player()
        keys = frozenset({"a", "b"})
        rules = InMemoryCardCatalogAdapter(
            keys,
            creature_keys=keys,
            creature_power_toughness_by_key={"a": (2, 2), "b": (1, 1)},
        )
        attacker = state.issue_object_id()
        b1 = state.issue_object_id()
        b2 = state.issue_object_id()
        state.register_object_at(
            Permanent(attacker, CardReference("a")),
            ZoneLocation(0, ZoneType.BATTLEFIELD),
        )
        for oid in (b1, b2):
            state.register_object_at(
                Permanent(oid, CardReference("b")),
                ZoneLocation(1, ZoneType.BATTLEFIELD),
            )
        state.apply_declare_attacker(0, attacker)
        BlockerDeclarationService().validate_and_apply(
            state,
            rules,
            defending_player_index=1,
            blocker_object_id=b1,
            attacker_object_id=attacker,
        )
        with pytest.raises(IllegalGameActionError, match="bloqueur"):
            BlockerDeclarationService().validate_and_apply(
                state,
                rules,
                defending_player_index=1,
                blocker_object_id=b2,
                attacker_object_id=attacker,
            )
