"""État global de partie : joueurs, pile, registre d'objets et journal."""

from __future__ import annotations

import random

from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_event import GameEvent
from baobab_mtg_rules_engine.domain.game_object import GameObject
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.player_state import PLAYER_OWNED_ZONE_TYPES, PlayerState
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.zone import Zone
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.insufficient_library_error import InsufficientLibraryError
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError


class GameState:  # pylint: disable=too-many-public-methods
    """État mutable et inspectable d'une partie à deux joueurs.

    Les identifiants d'objets sont émis de façon déterministe (compteur monotone).
    Les mutations exposées valident les invariants de base avant modification.

    :param players: Exactement deux :class:`PlayerState` indexés 0 et 1.
    """

    EXPECTED_PLAYER_COUNT: int = 2

    def __init__(self, players: tuple[PlayerState, PlayerState]) -> None:
        if len(players) != self.EXPECTED_PLAYER_COUNT:
            msg = "Ce modèle ne supporte pour l'instant qu'exactement deux joueurs."
            raise InvalidGameStateError(msg, field_name="players")
        if players[0].player_index != 0 or players[1].player_index != 1:
            msg = "Les joueurs doivent avoir les index 0 et 1 dans l'ordre donné."
            raise InvalidGameStateError(msg, field_name="players")
        self._players: tuple[PlayerState, PlayerState] = players
        self._stack: Zone = Zone(ZoneType.STACK, None)
        self._objects: dict[GameObjectId, GameObject] = {}
        self._next_object_id: int = 1
        self._events: list[GameEvent] = []
        self._event_sequence: int = 0
        self._turn: TurnState = TurnState.start_first_turn(0)
        self._duel_first_player_index: int = 0
        self._priority_player_index: int = self._turn.active_player_index
        self._consecutive_empty_stack_passes: int = 0

    @classmethod
    def new_two_player(
        cls,
        *,
        names: tuple[str, str] | None = None,
        life_totals: tuple[int, int] | None = None,
    ) -> GameState:
        """Fabrique un état initial standard à deux joueurs.

        :param names: Noms d'inspection ; défaut ``('Joueur 1', 'Joueur 2')``.
        :param life_totals: Points de vie initiaux ; défaut ``(20, 20)``.
        :return: État prêt à recevoir des objets.
        """
        resolved_names = names or ("Joueur 1", "Joueur 2")
        resolved_life = life_totals or (20, 20)
        players = (
            PlayerState(0, name=resolved_names[0], life_total=resolved_life[0]),
            PlayerState(1, name=resolved_names[1], life_total=resolved_life[1]),
        )
        state = cls(players)
        state._append_event(
            EventType.GAME_INITIALIZED,
            (
                ("player_count", state.EXPECTED_PLAYER_COUNT),
                ("starting_player", state._turn.active_player_index),
            ),
        )
        state.establish_duel_opening_player(state.turn_state.active_player_index)
        return state

    @property
    def players(self) -> tuple[PlayerState, PlayerState]:
        """:return: Tuple des deux joueurs."""
        return self._players

    @property
    def turn_state(self) -> TurnState:
        """:return: Snapshot du tour courant."""
        return self._turn

    @property
    def stack_zone(self) -> Zone:
        """:return: Zone pile globale."""
        return self._stack

    @property
    def events(self) -> tuple[GameEvent, ...]:
        """:return: Copie immuable du journal d'événements."""
        return tuple(self._events)

    @property
    def duel_first_player_index(self) -> int:
        """:return: Joueur qui a pris le premier tour du duel (règle de la pioche initiale)."""
        return self._duel_first_player_index

    @property
    def priority_player_index(self) -> int:
        """:return: Joueur qui détient la priorité (fenêtre de jeu)."""
        return self._priority_player_index

    @property
    def consecutive_empty_stack_passes(self) -> int:
        """:return: Passes consécutives à pile vide dans l'étape courante."""
        return self._consecutive_empty_stack_passes

    def establish_duel_opening_player(self, player_index: int) -> None:
        """Mémorise le joueur qui commence le duel (saut de pioche du premier tour).

        À appeler après positionnement final du premier tour (ex. setup usine).

        :param player_index: ``0`` ou ``1``.
        :raises InvalidGameStateError: si l'index est hors duel.
        """
        if player_index not in (0, 1):
            msg = "Index joueur invalide pour le duel à deux."
            raise InvalidGameStateError(msg, field_name="player_index")
        self._duel_first_player_index = player_index

    def turn_engine_set_priority_player(self, player_index: int) -> None:
        """Assigne la priorité (API réservée au moteur de boucle de tour)."""
        if player_index not in (0, 1):
            msg = "Index joueur invalide pour la priorité."
            raise InvalidGameStateError(msg, field_name="player_index")
        self._priority_player_index = player_index

    def turn_engine_reset_empty_stack_passes(self) -> None:
        """Remet à zéro le compteur de passes à pile vide (moteur de tour)."""
        self._consecutive_empty_stack_passes = 0

    def turn_engine_increment_empty_stack_passes(self) -> int:
        """Incrémente les passes à pile vide ; retourne la nouvelle valeur."""
        self._consecutive_empty_stack_passes += 1
        return self._consecutive_empty_stack_passes

    def record_engine_event(
        self,
        event_type: EventType,
        payload: tuple[tuple[str, str | int], ...] = (),
    ) -> None:
        """Ajoute un événement moteur au journal (setup, instrumentation, etc.).

        Complète les événements générés automatiquement par les mutations d'objets.

        :param event_type: Type fonctionnel à tracer.
        :param payload: Données contextuelles sérialisables.
        """
        self._append_event(event_type, payload)

    def shuffle_player_library(self, player_index: int, rng: random.Random) -> None:
        """Mélange la bibliothèque d'un joueur de façon déterministe via ``rng``.

        :param player_index: Joueur concerné.
        :param rng: Générateur pseudo-aléatoire déjà positionné.
        """
        library_zone = self._players[player_index].zone(ZoneType.LIBRARY)
        ordered = list(library_zone.object_ids())
        rng.shuffle(ordered)
        library_zone.replace_ordered_contents(tuple(ordered))

    def draw_cards_from_library_to_hand(
        self, player_index: int, count: int
    ) -> tuple[GameObjectId, ...]:
        """Pioche depuis le haut de la bibliothèque vers la main.

        Ne déclenche aucune règle de défaite : une pioche impossible lève une erreur
        de validation explicite (setup ou règles futures), après vérification du nombre
        de cartes disponibles (aucune mutation si la pioche est impossible).

        :param player_index: Joueur qui pioche.
        :param count: Nombre de cartes demandé.
        :return: Identifiants piochés dans l'ordre (premier = plus ancien sur le dessus).
        :raises InsufficientLibraryError: si la bibliothèque contient moins de ``count`` cartes.
        """
        if count < 0:
            msg = "Le nombre de cartes à piocher ne peut pas être négatif."
            raise InvalidGameStateError(msg, field_name="count")
        library_zone = self._players[player_index].zone(ZoneType.LIBRARY)
        available = library_zone.object_ids()
        if len(available) < count:
            msg = "Bibliothèque insuffisante pour la pioche demandée."
            raise InsufficientLibraryError(msg, field_name="library")
        drawn: list[GameObjectId] = []
        hand = ZoneLocation(player_index, ZoneType.HAND)
        for _ in range(count):
            library = self._players[player_index].zone(ZoneType.LIBRARY)
            current = library.object_ids()
            top = current[0]
            self.relocate_preserving_identity(top, hand)
            drawn.append(top)
        return tuple(drawn)

    def replace_turn_state(self, turn_state: TurnState) -> None:
        """Remplace le tour courant (transition explicite, hors logique de règles).

        :param turn_state: Nouvel état de tour.
        """
        self._turn = turn_state

    def issue_object_id(self) -> GameObjectId:
        """Attribue le prochain identifiant déterministe.

        :return: Nouvel identifiant unique dans cette partie.
        """
        object_id = GameObjectId(self._next_object_id)
        self._next_object_id += 1
        return object_id

    def get_object(self, object_id: GameObjectId) -> GameObject:
        """Accès au registre d'objets.

        :param object_id: Identifiant recherché.
        :return: Objet enregistré.
        :raises InvalidGameStateError: si l'objet est inconnu.
        """
        try:
            return self._objects[object_id]
        except KeyError as exc:
            msg = "Objet inconnu dans l'état de partie."
            raise InvalidGameStateError(msg, field_name="object_id") from exc

    def register_object_at(self, obj: GameObject, location: ZoneLocation) -> None:
        """Enregistre un objet neuf et le place dans une zone.

        :param obj: Objet portant un identifiant déjà issu pour cette partie.
        :param location: Zone cible cohérente avec le type de zone.
        :raises InvalidGameStateError: si l'identifiant existe déjà ou la zone est invalide.
        """
        self._validate_player_bounds(location)
        if obj.object_id in self._objects:
            msg = "Un objet avec cet identifiant existe déjà."
            raise InvalidGameStateError(msg, field_name="object_id")
        zone = self._zone_for_location(location)
        self._objects[obj.object_id] = obj
        zone.append(obj.object_id)
        self._append_event(
            EventType.OBJECT_REGISTERED,
            (
                ("object_id", obj.object_id.value),
                ("zone_type", location.zone_type.name),
                ("player_index", -1 if location.player_index is None else location.player_index),
                ("kind", obj.kind_label),
            ),
        )

    def find_location(self, object_id: GameObjectId) -> ZoneLocation:
        """Localise un objet dans l'état courant.

        :param object_id: Identifiant recherché.
        :return: Emplacement logique.
        :raises InvalidGameStateError: si l'objet n'est dans aucune zone.
        """
        if self._stack.contains(object_id):
            return ZoneLocation(None, ZoneType.STACK)
        for player in self._players:
            for zone_type in PLAYER_OWNED_ZONE_TYPES:
                zone = player.zone(zone_type)
                if zone.contains(object_id):
                    return ZoneLocation(player.player_index, zone_type)
        msg = "Objet introuvable dans les zones de la partie."
        raise InvalidGameStateError(msg, field_name="object_id")

    def relocate_preserving_identity(self, object_id: GameObjectId, target: ZoneLocation) -> None:
        """Déplace un objet en conservant son :class:`GameObjectId`.

        :param object_id: Objet à déplacer.
        :param target: Zone de destination.
        :raises InvalidGameStateError: si l'objet ou le placement est invalide.
        """
        self._validate_player_bounds(target)
        source = self.find_location(object_id)
        self._zone_for_location(source).remove(object_id)
        self._zone_for_location(target).append(object_id)
        self._append_event(
            EventType.OBJECT_RELOCATED,
            (
                ("object_id", object_id.value),
                ("from_zone", source.zone_type.name),
                (
                    "from_player",
                    -1 if source.player_index is None else source.player_index,
                ),
                ("to_zone", target.zone_type.name),
                ("to_player", -1 if target.player_index is None else target.player_index),
            ),
        )

    def migrate_in_game_card_as_new_instance(
        self,
        object_id: GameObjectId,
        *,
        target: ZoneLocation,
        new_kind: type[InGameCard],
    ) -> GameObjectId:
        """Retire une carte en jeu et en place une nouvelle instance (nouvel identifiant).

        Permet de modéliser explicitement un « nouvel objet logique » après changement
        de zone, distinct du simple déplacement qui préserve l'identité.

        :param object_id: Carte source à retirer du registre.
        :param target: Zone de destination de la nouvelle instance.
        :param new_kind: Sous-classe concrète de :class:`InGameCard` à instancier.
        :return: Identifiant de la nouvelle instance.
        :raises InvalidGameStateError: si la source n'est pas une carte en jeu.
        """
        self._validate_player_bounds(target)
        current = self.get_object(object_id)
        if not isinstance(current, InGameCard):
            msg = "Seule une carte en jeu peut être migrée vers une nouvelle identité."
            raise InvalidGameStateError(msg, field_name="object_id")
        if not issubclass(new_kind, InGameCard):
            msg = "new_kind doit hériter de InGameCard."
            raise InvalidGameStateError(msg, field_name="new_kind")
        source = self.find_location(object_id)
        self._zone_for_location(source).remove(object_id)
        del self._objects[object_id]
        new_id = self.issue_object_id()
        replacement = new_kind(new_id, current.card_reference)
        self._objects[new_id] = replacement
        self._zone_for_location(target).append(new_id)
        self._append_event(
            EventType.OBJECT_REPLACED_BY_NEW_IDENTITY,
            (
                ("old_object_id", object_id.value),
                ("new_object_id", new_id.value),
                ("to_zone", target.zone_type.name),
                ("to_player", -1 if target.player_index is None else target.player_index),
                ("kind", replacement.kind_label),
            ),
        )
        return new_id

    def _validate_player_bounds(self, location: ZoneLocation) -> None:
        if location.zone_type is ZoneType.STACK:
            return
        player_index = location.player_index
        if player_index is None:
            msg = "Zone joueur sans index de joueur."
            raise InvalidGameStateError(msg, field_name="player_index")
        if player_index >= self.EXPECTED_PLAYER_COUNT:
            msg = "Index joueur hors limite pour cette partie."
            raise InvalidGameStateError(msg, field_name="player_index")

    def _zone_for_location(self, location: ZoneLocation) -> Zone:
        if location.zone_type is ZoneType.STACK:
            return self._stack
        player_index = location.player_index
        if player_index is None:
            msg = "Zone joueur sans index de joueur."
            raise InvalidGameStateError(msg, field_name="player_index")
        return self._players[player_index].zone(location.zone_type)

    def _append_event(
        self,
        event_type: EventType,
        payload: tuple[tuple[str, str | int], ...],
    ) -> None:
        self._event_sequence += 1
        self._events.append(
            GameEvent(sequence=self._event_sequence, event_type=event_type, payload=payload)
        )
