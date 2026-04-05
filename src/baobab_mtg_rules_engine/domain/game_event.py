"""Événement de partie pour historique minimal."""

from dataclasses import dataclass

from baobab_mtg_rules_engine.domain.event_type import EventType


@dataclass(frozen=True, slots=True)
class GameEvent:
    """Événement immuable enregistré dans :class:`GameState`.

    La charge utile est une séquence de paires clé/valeur pour rester hashable
    et sérialisable sans surprise.

    :param sequence: Numéro monotone d'enregistrement dans la partie.
    :param event_type: Catégorie fonctionnelle de l'événement.
    :param payload: Données contextuelles (identifiants, zones, etc.).
    """

    sequence: int
    event_type: EventType
    payload: tuple[tuple[str, str | int], ...] = ()
