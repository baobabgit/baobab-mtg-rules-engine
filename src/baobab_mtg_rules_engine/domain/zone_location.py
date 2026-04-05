"""Emplacement logique d'un objet : joueur + type de zone ou pile globale."""

from dataclasses import dataclass

from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError


@dataclass(frozen=True, slots=True)
class ZoneLocation:
    """Référence immuable vers une zone dans l'état de partie.

    La pile (:attr:`ZoneType.STACK`) n'a pas de propriétaire : ``player_index``
    doit alors valoir ``None``. Les autres zones attendent un index joueur valide.

    :param player_index: Index du joueur propriétaire, ou ``None`` pour la pile.
    :param zone_type: Type de zone ciblé.
    """

    player_index: int | None
    zone_type: ZoneType

    def __post_init__(self) -> None:
        if self.zone_type is ZoneType.STACK:
            if self.player_index is not None:
                msg = "La pile ne doit pas avoir de joueur propriétaire."
                raise InvalidGameStateError(msg, field_name="player_index")
            return
        if self.player_index is None:
            msg = "Une zone autre que la pile doit avoir un joueur propriétaire."
            raise InvalidGameStateError(msg, field_name="player_index")
        if self.player_index < 0:
            msg = "player_index ne peut pas être négatif."
            raise InvalidGameStateError(msg, field_name="player_index")
