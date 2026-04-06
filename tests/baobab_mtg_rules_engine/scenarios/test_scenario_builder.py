"""Tests pour :class:`ScenarioBuilder` et :class:`ScenarioContext`."""

import pytest

from baobab_mtg_rules_engine.catalog.in_memory_card_catalog_adapter import (
    InMemoryCardCatalogAdapter,
)
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError
from baobab_mtg_rules_engine.scenarios.scenario_builder import ScenarioBuilder


class TestScenarioBuilder:
    """Construction et alias stables."""

    def test_build_requires_two_player_first(self) -> None:
        """Sans état initial, le build échoue."""
        rules = InMemoryCardCatalogAdapter(frozenset())
        with pytest.raises(InvalidGameStateError, match="with_two_player_game"):
            ScenarioBuilder(rules).build()

    def test_alias_resolves_to_hand_card(self) -> None:
        """La carte en main est retrouvable par alias."""
        rules = InMemoryCardCatalogAdapter(frozenset({"x"}))
        ctx = (
            ScenarioBuilder(rules)
            .with_two_player_game()
            .add_card_in_hand(0, "x", alias="c1")
            .build()
        )
        oid = ctx.object_aliases["c1"]
        assert ctx.state.find_location(oid).zone_type is ZoneType.HAND

    def test_turn_and_priority(self) -> None:
        """Le tour et la priorité sont positionnables."""
        rules = InMemoryCardCatalogAdapter(frozenset())
        ctx = (
            ScenarioBuilder(rules)
            .with_two_player_game()
            .with_turn_state(TurnState(1, 2, Step.UPKEEP))
            .with_priority_player(1)
            .build()
        )
        assert ctx.state.turn_state.active_player_index == 1
        assert ctx.state.priority_player_index == 1
        assert ctx.acting_player_index == 1

    def test_duplicate_alias_raises(self) -> None:
        """Deux objets ne peuvent pas partager le même alias."""
        rules = InMemoryCardCatalogAdapter(frozenset({"a", "b"}))
        builder = (
            ScenarioBuilder(rules).with_two_player_game().add_card_in_hand(0, "a", alias="dup")
        )
        with pytest.raises(InvalidGameStateError, match="Alias"):
            builder.add_card_in_hand(0, "b", alias="dup")

    def test_negative_floating_mana_raises(self) -> None:
        """Le mana ajouté doit être positif ou nul."""
        rules = InMemoryCardCatalogAdapter(frozenset())
        builder = ScenarioBuilder(rules).with_two_player_game()
        with pytest.raises(InvalidGameStateError, match="négatif"):
            builder.add_floating_mana(0, -1)

    def test_add_permanent_on_battlefield_registers_alias(self) -> None:
        """Un permanent sur le champ est adressable par alias."""
        rules = InMemoryCardCatalogAdapter(frozenset({"creature"}))
        ctx = (
            ScenarioBuilder(rules)
            .with_two_player_game()
            .add_permanent_on_battlefield(0, "creature", alias="grizzly")
            .build()
        )
        oid = ctx.object_aliases["grizzly"]
        assert ctx.state.find_location(oid).zone_type is ZoneType.BATTLEFIELD

    def test_duplicate_alias_on_permanent_raises(self) -> None:
        """Le même alias ne peut pas servir pour une carte et un permanent."""
        rules = InMemoryCardCatalogAdapter(frozenset({"a", "b"}))
        builder = (
            ScenarioBuilder(rules).with_two_player_game().add_card_in_hand(0, "a", alias="shared")
        )
        with pytest.raises(InvalidGameStateError, match="Alias"):
            builder.add_permanent_on_battlefield(0, "b", alias="shared")

    def test_with_duel_opening_player(self) -> None:
        """Le premier joueur du duel peut être fixé."""
        rules = InMemoryCardCatalogAdapter(frozenset())
        ctx = ScenarioBuilder(rules).with_two_player_game().with_duel_opening_player(1).build()
        assert ctx.state.duel_first_player_index == 1
