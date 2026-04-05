"""Adaptateur fonctionnel vers :class:`MulliganChoicePort` (structural typing)."""

from collections.abc import Callable

from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


class CallbackMulliganChoice:
    """Délègue à un callable Python pour les tests ou l'intégration."""

    def __init__(
        self,
        callback: Callable[
            [int, int, tuple[GameObjectId, ...]],
            bool,
        ],
    ) -> None:
        self._callback: Callable[
            [int, int, tuple[GameObjectId, ...]],
            bool,
        ] = callback

    def should_take_mulligan(
        self,
        player_index: int,
        *,
        mulligan_depth: int,
        hand_object_ids: tuple[GameObjectId, ...],
    ) -> bool:
        """:return: Résultat du callable fourni."""
        return self._callback(player_index, mulligan_depth, hand_object_ids)
