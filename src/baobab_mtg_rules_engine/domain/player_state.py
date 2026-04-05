"""État d'un joueur : points de vie, nom affichable et zones possédées."""

from baobab_mtg_rules_engine.domain.zone import Zone
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError

PLAYER_OWNED_ZONE_TYPES: tuple[ZoneType, ...] = (
    ZoneType.LIBRARY,
    ZoneType.HAND,
    ZoneType.GRAVEYARD,
    ZoneType.BATTLEFIELD,
    ZoneType.EXILE,
    ZoneType.COMMAND,
    ZoneType.SIDEBOARD,
)


class PlayerState:
    """Agrégat des zones et attributs scalaires d'un joueur.

    :param player_index: Index stable du joueur dans la partie (0 ou 1 pour deux joueurs).
    :param name: Nom ou pseudo pour inspection (hors stratégie IA).
    :param life_total: Points de vie courants.
    """

    def __init__(self, player_index: int, *, name: str, life_total: int = 20) -> None:
        if player_index < 0:
            msg = "player_index ne peut pas être négatif."
            raise InvalidGameStateError(msg, field_name="player_index")
        if life_total < 0:
            msg = "life_total ne peut pas être négatif."
            raise InvalidGameStateError(msg, field_name="life_total")
        self._player_index: int = player_index
        self._name: str = name
        self._life_total: int = life_total
        self._floating_mana: int = 0
        self._zones: dict[ZoneType, Zone] = {
            zone_type: Zone(zone_type, player_index) for zone_type in PLAYER_OWNED_ZONE_TYPES
        }

    @property
    def player_index(self) -> int:
        """:return: Index du joueur."""
        return self._player_index

    @property
    def name(self) -> str:
        """:return: Nom d'inspection du joueur."""
        return self._name

    @property
    def life_total(self) -> int:
        """:return: Points de vie actuels."""
        return self._life_total

    @property
    def floating_mana(self) -> int:
        """:return: Mana résiduel simplifié (unités entières, vidé au nettoyage)."""
        return self._floating_mana

    def add_floating_mana(self, amount: int) -> None:
        """Ajoute du mana flottant (modèle minimal pour tests et futur pool).

        :param amount: Quantité strictement positive.
        :raises InvalidGameStateError: si ``amount`` n'est pas positive.
        """
        if amount < 1:
            msg = "Le mana ajouté doit être au moins 1."
            raise InvalidGameStateError(msg, field_name="amount")
        self._floating_mana += amount

    def clear_floating_mana(self) -> None:
        """Remet le mana résiduel à zéro (étape de nettoyage)."""
        self._floating_mana = 0

    def spend_floating_mana(self, amount: int) -> None:
        """Dépense du mana flottant.

        :param amount: Quantité positive.
        :raises InvalidGameStateError: si le montant est invalide ou le pool insuffisant.
        """
        if amount < 0:
            msg = "Le mana à dépenser ne peut pas être négatif."
            raise InvalidGameStateError(msg, field_name="amount")
        if amount == 0:
            return
        if self._floating_mana < amount:
            msg = "Mana flottant insuffisant pour ce coût."
            raise InvalidGameStateError(msg, field_name="floating_mana")
        self._floating_mana -= amount

    def zone(self, zone_type: ZoneType) -> Zone:
        """Accès à une zone possédée par ce joueur.

        :param zone_type: Type de zone demandé (hors pile).
        :return: Zone correspondante.
        :raises InvalidGameStateError: si ``zone_type`` est la pile.
        """
        if zone_type is ZoneType.STACK:
            msg = "La pile n'est pas une zone possédée par un joueur."
            raise InvalidGameStateError(msg, field_name="zone_type")
        return self._zones[zone_type]
