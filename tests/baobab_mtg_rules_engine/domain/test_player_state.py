"""Tests pour :class:`PlayerState`."""

import pytest

from baobab_mtg_rules_engine.domain.player_state import PlayerState
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError


class TestPlayerState:
    """Zones possédées et validations de base."""

    def test_default_zones_exist(self) -> None:
        """Chaque zone joueur attendue est initialisée."""
        player = PlayerState(0, name="Alice")
        hand = player.zone(ZoneType.HAND)
        assert hand.zone_type is ZoneType.HAND
        assert hand.owner_player_index == 0

    def test_stack_zone_forbidden(self) -> None:
        """La pile n'est pas accessible via :meth:`PlayerState.zone`."""
        player = PlayerState(0, name="Bob")
        with pytest.raises(InvalidGameStateError, match="pile"):
            player.zone(ZoneType.STACK)

    def test_negative_life_rejected(self) -> None:
        """Les points de vie négatifs sont refusés à la construction."""
        with pytest.raises(InvalidGameStateError, match="life_total"):
            PlayerState(0, name="x", life_total=-1)

    def test_negative_player_index_rejected(self) -> None:
        """Un index joueur négatif est refusé."""
        with pytest.raises(InvalidGameStateError, match="player_index"):
            PlayerState(-1, name="x")

    def test_add_floating_mana_positive(self) -> None:
        """Le mana flottant s'accumule puis se vide."""
        player = PlayerState(0, name="Mana")
        player.add_floating_mana(2)
        assert player.floating_mana == 2
        player.clear_floating_mana()
        assert player.floating_mana == 0

    def test_add_floating_mana_non_positive_rejected(self) -> None:
        """Quantité de mana nulle ou négative refusée."""
        player = PlayerState(0, name="Mana")
        with pytest.raises(InvalidGameStateError, match="mana"):
            player.add_floating_mana(0)

    def test_apply_damage_reduces_life(self) -> None:
        """Les dégâts réduisent les points de vie sans passer sous zéro."""
        player = PlayerState(0, name="Dmg", life_total=10)
        player.apply_damage(3)
        assert player.life_total == 7
        player.apply_damage(99)
        assert player.life_total == 0

    def test_apply_damage_negative_rejected(self) -> None:
        """Les dégâts négatifs sont refusés."""
        player = PlayerState(0, name="x", life_total=5)
        with pytest.raises(InvalidGameStateError, match="dégâts"):
            player.apply_damage(-1)
