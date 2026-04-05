"""Modèle commun des actions de jeu exposées au calculateur légal."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind


class GameAction(ABC):
    """Action atomique qu'un agent peut tenter après validation par :class:`LegalActionService`."""

    @property
    @abstractmethod
    def kind(self) -> SupportedActionKind:
        """:return: Famille d'action pour le catalogue et le tri."""

    @abstractmethod
    def sort_key(self) -> tuple[Any, ...]:
        """:return: Clé de tri déterministe (plus petit = premier dans la liste légale)."""
