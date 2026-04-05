"""Décisions de mulligan fournies depuis l'extérieur du moteur (pas d'IA interne)."""

from typing import Protocol, runtime_checkable

from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


@runtime_checkable
class MulliganChoicePort(Protocol):
    """Stratégie de mulligan injectée (joueur humain, script de test, etc.)."""

    def should_take_mulligan(
        self,
        player_index: int,
        *,
        mulligan_depth: int,
        hand_object_ids: tuple[GameObjectId, ...],
    ) -> bool:
        """Indique si le joueur prend un mulligan supplémentaire.

        :param player_index: ``0`` ou ``1``.
        :param mulligan_depth: Nombre de mulligans déjà pris avant cette décision.
        :param hand_object_ids: Main actuelle (identifiants stables).
        :return: ``True`` pour mulligan, ``False`` pour garder.
        """
