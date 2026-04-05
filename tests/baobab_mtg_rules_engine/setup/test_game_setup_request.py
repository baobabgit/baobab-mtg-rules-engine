"""Tests pour :class:`GameSetupRequest`."""

import pytest

from baobab_mtg_rules_engine.setup.deck_definition import DeckDefinition
from baobab_mtg_rules_engine.setup.game_setup_request import GameSetupRequest


class TestGameSetupRequest:
    """Validation des paramètres de requête de setup."""

    def _minimal_decks(self) -> tuple[DeckDefinition, DeckDefinition]:
        entries = tuple((f"c{i}", 4) for i in range(15))
        d = DeckDefinition("a", entries)
        return d, d

    def test_empty_game_id_rejected(self) -> None:
        """Un ``game_id`` vide ou blanc est refusé."""
        decks = self._minimal_decks()
        with pytest.raises(ValueError, match="game_id"):
            GameSetupRequest(
                game_id="   ",
                player_names=("a", "b"),
                decks=decks,
                rng_seed=1,
            )

    def test_starting_player_must_be_0_1_or_none(self) -> None:
        """Seuls ``0``, ``1`` ou ``None`` sont acceptés pour le premier joueur."""
        decks = self._minimal_decks()
        with pytest.raises(ValueError, match="starting_player"):
            GameSetupRequest(
                game_id="g",
                player_names=("a", "b"),
                decks=decks,
                rng_seed=1,
                starting_player=2,
            )
