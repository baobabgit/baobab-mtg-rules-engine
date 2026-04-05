"""Paramètres d'entrée pour la création déterministe d'une partie."""

from dataclasses import dataclass

from baobab_mtg_rules_engine.setup.deck_definition import DeckDefinition


@dataclass(frozen=True, slots=True)
class GameSetupRequest:
    """Requête de setup : identité, decks, graine et joueur initial optionnel.

    :param game_id: Identifiant de session.
    :param player_names: Noms des joueurs (index ``0`` puis ``1``).
    :param decks: Deck principal du joueur ``0`` puis du joueur ``1``.
    :param rng_seed: Graine pour le mélange et le tirage du premier joueur.
    :param starting_player: Force le joueur qui commence ; ``None`` pour tirage pseudo-aléatoire.
    """

    game_id: str
    player_names: tuple[str, str]
    decks: tuple[DeckDefinition, DeckDefinition]
    rng_seed: int
    starting_player: int | None = None

    def __post_init__(self) -> None:
        if not self.game_id.strip():
            msg = "game_id ne doit pas être vide."
            raise ValueError(msg)
        if self.starting_player is not None and self.starting_player not in (0, 1):
            msg = "starting_player doit valoir 0, 1 ou None."
            raise ValueError(msg)
