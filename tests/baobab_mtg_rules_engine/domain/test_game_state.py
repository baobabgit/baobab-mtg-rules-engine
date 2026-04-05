"""Tests pour :class:`GameState`."""

from typing import Any, cast
from unittest.mock import Mock

import pytest

from baobab_mtg_rules_engine.domain.ability_on_stack import AbilityOnStack
from baobab_mtg_rules_engine.domain.card_reference import CardReference
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.player_state import PlayerState
from baobab_mtg_rules_engine.domain.spell_on_stack import SpellOnStack
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError


class TestGameState:
    """Construction, déplacements et journal d'événements."""

    def test_new_two_player_initial_state(self) -> None:
        """Une partie à deux joueurs possède des zones et un journal initial."""
        state = GameState.new_two_player(names=("Asha", "Bo"), life_totals=(19, 20))
        assert state.players[0].name == "Asha"
        assert state.players[0].life_total == 19
        assert state.players[1].player_index == 1
        assert state.events[0].event_type is EventType.GAME_INITIALIZED
        assert state.stack_zone.zone_type is ZoneType.STACK

    def test_constructor_requires_ordered_player_indices(self) -> None:
        """Les index joueur doivent être ``0`` puis ``1`` dans le tuple."""
        first = PlayerState(0, name="p0")
        wrong_second = PlayerState(0, name="also0")
        with pytest.raises(InvalidGameStateError, match="index"):
            GameState((first, wrong_second))

    def test_constructor_requires_exactly_two_players(self) -> None:
        """Seuls deux joueurs sont supportés à ce stade."""
        players = (
            PlayerState(0, name="a"),
            PlayerState(1, name="b"),
            PlayerState(2, name="c"),
        )
        with pytest.raises(InvalidGameStateError, match="deux joueurs"):
            GameState(cast(Any, players))

    def test_register_relocate_preserves_identity(self) -> None:
        """Un déplacement conserve le même :class:`GameObjectId`."""
        state = GameState.new_two_player()
        ref = CardReference("spell:1")
        oid = state.issue_object_id()
        spell = SpellOnStack(oid, ref)
        hand = ZoneLocation(0, ZoneType.HAND)
        state.register_object_at(spell, hand)
        battlefield = ZoneLocation(0, ZoneType.BATTLEFIELD)
        state.relocate_preserving_identity(oid, battlefield)
        assert state.find_location(oid).zone_type is ZoneType.BATTLEFIELD
        relocated = state.get_object(oid)
        assert isinstance(relocated, SpellOnStack)
        assert relocated.card_reference == ref

    def test_migrate_creates_new_logical_object(self) -> None:
        """La migration avec nouvelle identité produit un nouvel identifiant."""
        state = GameState.new_two_player()
        old_id = state.issue_object_id()
        spell = SpellOnStack(old_id, CardReference("lightning"))
        state.register_object_at(spell, ZoneLocation(None, ZoneType.STACK))
        target = ZoneLocation(1, ZoneType.BATTLEFIELD)
        new_id = state.migrate_in_game_card_as_new_instance(
            old_id,
            target=target,
            new_kind=Permanent,
        )
        assert new_id != old_id
        perm = state.get_object(new_id)
        assert isinstance(perm, Permanent)
        assert perm.card_reference.catalog_key == "lightning"
        assert state.find_location(new_id).player_index == 1
        with pytest.raises(InvalidGameStateError):
            state.get_object(old_id)

    def test_get_object_unknown_raises(self) -> None:
        """Un identifiant inconnu lève une erreur de domaine."""
        state = GameState.new_two_player()
        with pytest.raises(InvalidGameStateError, match="inconnu"):
            state.get_object(GameObjectId(1))

    def test_find_location_unknown_raises(self) -> None:
        """Un objet absent de toute zone est introuvable."""
        state = GameState.new_two_player()
        with pytest.raises(InvalidGameStateError, match="introuvable"):
            state.find_location(GameObjectId(1))

    def test_register_duplicate_id_raises(self) -> None:
        """Deux enregistrements avec le même identifiant sont interdits."""
        state = GameState.new_two_player()
        oid = state.issue_object_id()
        first = SpellOnStack(oid, CardReference("a"))
        duplicate = SpellOnStack(oid, CardReference("b"))
        state.register_object_at(first, ZoneLocation(0, ZoneType.HAND))
        with pytest.raises(InvalidGameStateError, match="existe déjà"):
            state.register_object_at(duplicate, ZoneLocation(1, ZoneType.HAND))

    def test_relocate_rejects_invalid_player_index(self) -> None:
        """Une zone joueur hors limites est refusée."""
        state = GameState.new_two_player()
        oid = state.issue_object_id()
        state.register_object_at(
            SpellOnStack(oid, CardReference("x")),
            ZoneLocation(None, ZoneType.STACK),
        )
        bad_target = ZoneLocation(99, ZoneType.HAND)
        with pytest.raises(InvalidGameStateError, match="hors limite"):
            state.relocate_preserving_identity(oid, bad_target)

    def test_migrate_rejects_non_card_object(self) -> None:
        """Seules les cartes en jeu peuvent être migrées avec nouvelle identité."""
        state = GameState.new_two_player()
        oid = state.issue_object_id()
        ability = AbilityOnStack(oid, ability_key="trigger")
        state.register_object_at(ability, ZoneLocation(None, ZoneType.STACK))
        with pytest.raises(InvalidGameStateError, match="carte"):
            state.migrate_in_game_card_as_new_instance(
                oid,
                target=ZoneLocation(0, ZoneType.HAND),
                new_kind=Permanent,
            )

    def test_migrate_rejects_non_in_game_card_kind(self) -> None:
        """``new_kind`` doit être une sous-classe de :class:`InGameCard`."""
        state = GameState.new_two_player()
        oid = state.issue_object_id()
        state.register_object_at(
            SpellOnStack(oid, CardReference("z")),
            ZoneLocation(0, ZoneType.HAND),
        )
        with pytest.raises(InvalidGameStateError, match="new_kind"):
            state.migrate_in_game_card_as_new_instance(
                oid,
                target=ZoneLocation(0, ZoneType.BATTLEFIELD),
                new_kind=cast(type[InGameCard], dict),
            )

    def test_replace_turn_state(self) -> None:
        """Le tour peut être remplacé explicitement."""
        state = GameState.new_two_player()
        updated = TurnState(active_player_index=1, turn_number=2, step=Step.MAIN_PRECOMBAT)
        state.replace_turn_state(updated)
        assert state.turn_state.active_player_index == 1
        assert state.turn_state.turn_number == 2

    def test_register_rejects_non_stack_zone_without_player_index(self) -> None:
        """Garde-fou interne si un emplacement main n'a pas d'index joueur."""
        state = GameState.new_two_player()
        broken_location = Mock()
        broken_location.zone_type = ZoneType.HAND
        broken_location.player_index = None
        oid = state.issue_object_id()
        spell = SpellOnStack(oid, CardReference("orphan"))
        with pytest.raises(InvalidGameStateError, match="sans index"):
            state.register_object_at(spell, broken_location)  # type: ignore[arg-type]

    def test_zone_for_location_rejects_hand_without_player(self) -> None:
        """La résolution de zone refuse une main sans index joueur (défense en profondeur)."""
        state = GameState.new_two_player()
        loc = Mock()
        loc.zone_type = ZoneType.HAND
        loc.player_index = None
        with pytest.raises(InvalidGameStateError, match="sans index"):
            state._zone_for_location(loc)  # type: ignore[arg-type]  # pylint: disable=protected-access
