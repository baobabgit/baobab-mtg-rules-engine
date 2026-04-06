"""Contexte de scénario : état, règles et services prêts pour replay ou tests."""

from __future__ import annotations

from dataclasses import dataclass

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.engine.legal_action_service import LegalActionService
from baobab_mtg_rules_engine.engine.turn_manager import TurnManager


@dataclass(frozen=True, slots=True)
class ScenarioContext:
    """Regroupe l'état et les services nécessaires pour appliquer des actions légales.

    :param state: État de partie inspectable.
    :param rules: Port catalogue gameplay.
    :param object_aliases: Correspondance nom stable → identifiant d'objet pour le replay.
    :param turn_manager: Orchestrateur de tour lié à ``state``.
    :param legal_service: Service de légalité / application d'actions.
    """

    state: GameState
    rules: CardGameplayPort
    object_aliases: dict[str, GameObjectId]
    turn_manager: TurnManager
    legal_service: LegalActionService

    @property
    def acting_player_index(self) -> int:
        """:return: Index du joueur qui détient la priorité."""
        return self.state.priority_player_index
