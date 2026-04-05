"""Ordre des étapes et passage au tour suivant après nettoyage."""

from baobab_mtg_rules_engine.domain.step import STANDARD_DUEL_STEP_ORDER, Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.exceptions.unsupported_rule_exception import UnsupportedRuleException


class StepTransitionService:
    """Séquence déterministe des étapes en duel (hors raccourcis tournoi)."""

    _STEP_ORDER: tuple[Step, ...] = STANDARD_DUEL_STEP_ORDER

    def successor_step(self, current: Step) -> Step | None:
        """Étape suivante dans le même tour, ou ``None`` après :attr:`Step.CLEANUP`.

        :param current: Étape en cours.
        :return: Prochaine étape, ou ``None`` si le tour structurel se termine ici.
        :raises UnsupportedRuleException: si l'étape n'est pas dans la séquence supportée.
        """
        try:
            idx = self._STEP_ORDER.index(current)
        except ValueError as exc:
            msg = f"Étape non supportée dans la boucle de tour : {current!r}."
            raise UnsupportedRuleException(msg, rule_reference="turn-loop-step") from exc
        if idx + 1 < len(self._STEP_ORDER):
            return self._STEP_ORDER[idx + 1]
        return None

    def turn_state_after_cleanup(self, ts: TurnState) -> TurnState:
        """Construit le premier état du joueur suivant après la fin du tour courant.

        :param ts: Tour se terminant en :attr:`Step.CLEANUP`.
        :return: Premier état (``UNTAP``) du joueur adverse, numéro de tour incrémenté.
        """
        next_active = 1 - ts.active_player_index
        next_turn_number = ts.turn_number + 1
        return TurnState(
            active_player_index=next_active,
            turn_number=next_turn_number,
            step=Step.UNTAP,
        )
