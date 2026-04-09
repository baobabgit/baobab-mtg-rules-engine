"""État global de partie : joueurs, pile, registre d'objets et journal."""

from __future__ import annotations

import random

from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_event import GameEvent
from baobab_mtg_rules_engine.domain.game_object import GameObject
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.pending_triggered_ability import PendingTriggeredAbility
from baobab_mtg_rules_engine.domain.permanent import Permanent
from baobab_mtg_rules_engine.domain.player_state import PLAYER_OWNED_ZONE_TYPES, PlayerState
from baobab_mtg_rules_engine.domain.spell_on_stack import SpellOnStack
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.domain.triggered_ability_stack_object import (
    TriggeredAbilityStackObject,
)
from baobab_mtg_rules_engine.domain.zone import Zone
from baobab_mtg_rules_engine.domain.zone_location import ZoneLocation
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.insufficient_library_error import InsufficientLibraryError
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError
from baobab_mtg_rules_engine.stack.stack_object import StackObject


class GameState:  # pylint: disable=too-many-public-methods,too-many-instance-attributes
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
        self._consecutive_non_empty_stack_passes: int = 0
        self._lands_played_this_turn: int = 0
        self._declared_attackers: list[GameObjectId] = []
        self._declared_blocks: list[tuple[GameObjectId, GameObjectId]] = []
        self._stack_object_views: dict[GameObjectId, StackObject] = {}
        self._triggered_ability_views: dict[GameObjectId, TriggeredAbilityStackObject] = {}
        self._pending_triggers: list[PendingTriggeredAbility] = []
        self._next_pending_trigger_id: int = 1
        self._trigger_scan_sequence: int = 0
        self._winner_player_index: int | None = None
        self._is_draw: bool = False

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

    @property
    def consecutive_non_empty_stack_passes(self) -> int:
        """:return: Passes consécutives avec pile non vide dans la fenêtre courante."""
        return self._consecutive_non_empty_stack_passes

    @property
    def lands_played_this_turn(self) -> int:
        """:return: Terrains joués par le joueur actif durant ce tour."""
        return self._lands_played_this_turn

    @property
    def declared_attackers(self) -> tuple[GameObjectId, ...]:
        """:return: Attaquants déclarés pour le combat courant (modèle simplifié)."""
        return tuple(self._declared_attackers)

    @property
    def declared_blocks(self) -> tuple[tuple[GameObjectId, GameObjectId], ...]:
        """:return: Paires (bloqueur, attaquant) déclarées."""
        return tuple(self._declared_blocks)

    @property
    def winner_player_index(self) -> int | None:
        """:return: Index du vainqueur si la partie est décidée sans match nul, sinon ``None``."""
        return self._winner_player_index

    @property
    def is_draw_game(self) -> bool:
        """:return: ``True`` si la partie s'est terminée par match nul (ex. deux joueurs à 0 PV)."""
        return self._is_draw

    @property
    def is_game_finished(self) -> bool:
        """:return: ``True`` si un vainqueur est désigné ou match nul enregistré."""
        return self._winner_player_index is not None or self._is_draw

    def record_player_defeat(self, loser_player_index: int, *, reason: str) -> None:
        """Enregistre la défaite d'un joueur et le vainqueur adverse (idempotent si déjà terminé).

        :param loser_player_index: ``0`` ou ``1``.
        :param reason: Libellé court pour le journal (ex. ``life``, ``library``).
        :raises InvalidGameStateError: si l'index est invalide.
        """
        if loser_player_index not in (0, 1):
            msg = "Index joueur invalide pour une défaite."
            raise InvalidGameStateError(msg, field_name="loser_player_index")
        if self.is_game_finished:
            return
        self._winner_player_index = 1 - loser_player_index
        self.record_engine_event(
            EventType.PLAYER_DEFEATED,
            (
                ("loser_player_index", loser_player_index),
                ("reason", reason),
            ),
        )
        self.record_engine_event(
            EventType.GAME_VICTORY_ASSIGNED,
            (("winner_player_index", self._winner_player_index),),
        )

    def record_draw_game(self) -> None:
        """Termine la partie sans vainqueur (idempotent si déjà terminé)."""
        if self.is_game_finished:
            return
        self._is_draw = True
        self.record_engine_event(EventType.GAME_DRAW, ())

    def clear_all_marked_damage_on_battlefield(self) -> None:
        """Remet à zéro les blessures marquées sur tous les permanents (fin de tour simplifiée)."""
        cleared = 0
        for player in self._players:
            for oid in player.zone(ZoneType.BATTLEFIELD).object_ids():
                obj = self.get_object(oid)
                if isinstance(obj, Permanent) and obj.marked_damage > 0:
                    obj.clear_marked_damage()
                    cleared += 1
        if cleared > 0:
            self.record_engine_event(
                EventType.ALL_PERMANENT_DAMAGE_CLEARED,
                (("permanents_affected", cleared),),
            )

    def _assert_combat_declarations_allowed(self) -> None:
        if self.is_game_finished:
            msg = "La partie est terminée : plus de déclarations de combat."
            raise InvalidGameStateError(msg, field_name="game")

    def turn_engine_reset_turn_resource_counters(self) -> None:
        """Remet les compteurs de tour (terrains) ; appelé en début de tour adverse."""
        self._lands_played_this_turn = 0

    def turn_engine_begin_combat_declarations(self) -> None:
        """Vide les déclarations de combat pour une nouvelle manœuvre de combat."""
        self._declared_attackers.clear()
        self._declared_blocks.clear()

    def turn_engine_spend_floating_mana(self, player_index: int, amount: int) -> None:
        """Délègue la dépense de mana flottant au joueur indiqué."""
        self._players[player_index].spend_floating_mana(amount)

    def attach_stack_object_view(
        self, spell_stack_object_id: GameObjectId, view: StackObject
    ) -> None:
        """Associe une vue :class:`StackObject` à un sort présent sur la pile.

        :raises InvalidGameStateError: si un enregistrement existe déjà pour cet identifiant.
        """
        if spell_stack_object_id in self._stack_object_views:
            msg = "Une vue de pile existe déjà pour cet identifiant de sort."
            raise InvalidGameStateError(msg, field_name="spell_stack_object_id")
        self._stack_object_views[spell_stack_object_id] = view

    def detach_stack_object_view(self, spell_stack_object_id: GameObjectId) -> StackObject | None:
        """Retire la vue associée ; retourne la vue si elle existait."""
        return self._stack_object_views.pop(spell_stack_object_id, None)

    def get_stack_object_view(self, spell_stack_object_id: GameObjectId) -> StackObject | None:
        """:return: La vue enregistrée ou ``None``."""
        return self._stack_object_views.get(spell_stack_object_id)

    @property
    def stack_object_views(self) -> tuple[StackObject, ...]:
        """:return: Copie immuable des vues de pile (ordre non garanti)."""
        return tuple(self._stack_object_views.values())

    @property
    def triggered_ability_stack_views(self) -> tuple[TriggeredAbilityStackObject, ...]:
        """:return: Vues de capacités déclenchées présentes sur la pile."""
        return tuple(self._triggered_ability_views.values())

    @property
    def pending_triggers(self) -> tuple[PendingTriggeredAbility, ...]:
        """:return: Copie immuable de la file de triggers détectés mais non empilés."""
        return tuple(self._pending_triggers)

    def issue_pending_trigger_id(self) -> int:
        """:return: Identifiant monotone d'entrée de trigger en attente."""
        pending_id = self._next_pending_trigger_id
        self._next_pending_trigger_id += 1
        return pending_id

    @property
    def trigger_scan_sequence(self) -> int:
        """:return: Dernier numéro de séquence d'événement déjà scanné pour les triggers."""
        return self._trigger_scan_sequence

    def mark_trigger_scan_sequence(self, sequence: int) -> None:
        """Mémorise le dernier événement analysé par le détecteur de triggers."""
        if sequence < 0:
            msg = "La séquence de scan de triggers ne peut pas être négative."
            raise InvalidGameStateError(msg, field_name="sequence")
        self._trigger_scan_sequence = sequence

    def queue_pending_trigger(self, pending_trigger: PendingTriggeredAbility) -> None:
        """Ajoute un trigger à la file d'attente en conservant l'ordre d'insertion."""
        self._pending_triggers.append(pending_trigger)

    def pop_all_pending_triggers(self) -> tuple[PendingTriggeredAbility, ...]:
        """Vide la file des triggers en attente et retourne son contenu ordonné."""
        queued = tuple(self._pending_triggers)
        self._pending_triggers.clear()
        return queued

    def attach_triggered_ability_view(
        self,
        ability_stack_object_id: GameObjectId,
        view: TriggeredAbilityStackObject,
    ) -> None:
        """Associe une vue de capacité déclenchée à un objet ``AbilityOnStack``."""
        if ability_stack_object_id in self._triggered_ability_views:
            msg = "Une vue de capacité déclenchée existe déjà pour cet identifiant."
            raise InvalidGameStateError(msg, field_name="ability_stack_object_id")
        self._triggered_ability_views[ability_stack_object_id] = view

    def detach_triggered_ability_view(
        self,
        ability_stack_object_id: GameObjectId,
    ) -> TriggeredAbilityStackObject | None:
        """Retire la vue de capacité déclenchée associée ; retourne la vue si présente."""
        return self._triggered_ability_views.pop(ability_stack_object_id, None)

    def get_triggered_ability_view(
        self,
        ability_stack_object_id: GameObjectId,
    ) -> TriggeredAbilityStackObject | None:
        """:return: Vue déclenchée associée à un objet de pile, ou ``None``."""
        return self._triggered_ability_views.get(ability_stack_object_id)

    def remove_object_from_stack(self, object_id: GameObjectId) -> None:
        """Retire un objet de la pile et du registre (usage : capacités sur la pile).

        :raises InvalidGameStateError: si l'objet n'est pas présent sur la pile.
        """
        loc = self.find_location(object_id)
        if loc.zone_type is not ZoneType.STACK:
            msg = "L'objet à retirer doit être présent sur la pile."
            raise InvalidGameStateError(msg, field_name="object_id")
        self._stack.remove(object_id)
        self.detach_stack_object_view(object_id)
        self.detach_triggered_ability_view(object_id)
        self._objects.pop(object_id, None)

    def apply_play_land(self, player_index: int, land_object_id: GameObjectId) -> None:
        """Joue un terrain depuis la main vers le champ (identité conservée, modèle simplifié).

        L'appelant doit avoir validé la légalité au préalable.

        :raises InvalidGameStateError: si la carte n'est pas une :class:`InGameCard` en main.
        """
        loc = self.find_location(land_object_id)
        if loc.zone_type is not ZoneType.HAND or loc.player_index != player_index:
            msg = "Le terrain doit être en main du joueur qui le joue."
            raise InvalidGameStateError(msg, field_name="land_object_id")
        obj = self.get_object(land_object_id)
        if not isinstance(obj, InGameCard):
            msg = "Seule une carte en main peut être jouée comme terrain."
            raise InvalidGameStateError(msg, field_name="land_object_id")
        bf = ZoneLocation(player_index, ZoneType.BATTLEFIELD)
        self.relocate_preserving_identity(land_object_id, bf)
        self._lands_played_this_turn += 1
        self.record_engine_event(
            EventType.LAND_PLAYED,
            (
                ("player_index", player_index),
                ("object_id", land_object_id.value),
                ("catalog_key", obj.card_reference.catalog_key),
            ),
        )

    def apply_cast_spell_hand_to_stack(
        self,
        player_index: int,
        spell_object_id: GameObjectId,
        *,
        generic_mana_cost: int,
    ) -> GameObjectId:
        """Lance un sort : main → pile, nouveau :class:`SpellOnStack`, paiement du coût.

        :return: Nouvel identifiant sur la pile.
        :raises InvalidGameStateError: si la carte n'est pas en main ou coût invalide.
        """
        loc = self.find_location(spell_object_id)
        if loc.zone_type is not ZoneType.HAND or loc.player_index != player_index:
            msg = "Le sort doit être en main du lanceur."
            raise InvalidGameStateError(msg, field_name="spell_object_id")
        if generic_mana_cost < 0:
            msg = "Coût de sort invalide."
            raise InvalidGameStateError(msg, field_name="generic_mana_cost")
        self.turn_engine_spend_floating_mana(player_index, generic_mana_cost)
        stack = ZoneLocation(None, ZoneType.STACK)
        new_id = self.migrate_in_game_card_as_new_instance(
            spell_object_id,
            target=stack,
            new_kind=SpellOnStack,
        )
        card = self.get_object(new_id)
        ref = card.card_reference if isinstance(card, SpellOnStack) else None
        ck = ref.catalog_key if ref is not None else ""
        self.record_engine_event(
            EventType.SPELL_CAST,
            (
                ("player_index", player_index),
                ("new_object_id", new_id.value),
                ("mana_paid", generic_mana_cost),
                ("catalog_key", ck),
            ),
        )
        return new_id

    def apply_activate_simple_ability(
        self,
        player_index: int,
        permanent_object_id: GameObjectId,
        *,
        generic_mana_cost: int,
    ) -> None:
        """Paie un coût pour une capacité simple sur un permanent contrôlé."""
        loc = self.find_location(permanent_object_id)
        if loc.zone_type is not ZoneType.BATTLEFIELD or loc.player_index != player_index:
            msg = "Le permanent doit être sur votre champ de bataille."
            raise InvalidGameStateError(msg, field_name="permanent_object_id")
        obj = self.get_object(permanent_object_id)
        if not isinstance(obj, Permanent):
            msg = "La capacité simple cible un permanent."
            raise InvalidGameStateError(msg, field_name="permanent_object_id")
        if generic_mana_cost < 0:
            msg = "Coût de capacité invalide."
            raise InvalidGameStateError(msg, field_name="generic_mana_cost")
        self.turn_engine_spend_floating_mana(player_index, generic_mana_cost)
        self.record_engine_event(
            EventType.SIMPLE_ABILITY_ACTIVATED,
            (
                ("player_index", player_index),
                ("permanent_id", permanent_object_id.value),
                ("mana_paid", generic_mana_cost),
                ("catalog_key", obj.card_reference.catalog_key),
            ),
        )

    def apply_declare_attacker(
        self,
        active_player_index: int,
        creature_object_id: GameObjectId,
    ) -> None:
        """Enregistre un attaquant (étape déclaration simplifiée)."""
        self._assert_combat_declarations_allowed()
        loc = self.find_location(creature_object_id)
        if loc.zone_type is not ZoneType.BATTLEFIELD or loc.player_index != active_player_index:
            msg = "L'attaquant doit être une créature sur le champ du joueur actif."
            raise InvalidGameStateError(msg, field_name="creature_object_id")
        obj = self.get_object(creature_object_id)
        if not isinstance(obj, Permanent):
            msg = "Seul un permanent peut attaquer."
            raise InvalidGameStateError(msg, field_name="creature_object_id")
        if creature_object_id in self._declared_attackers:
            msg = "Cette créature est déjà déclarée attaquante."
            raise InvalidGameStateError(msg, field_name="creature_object_id")
        self._declared_attackers.append(creature_object_id)
        self.record_engine_event(
            EventType.ATTACKER_DECLARED,
            (("object_id", creature_object_id.value),),
        )

    def apply_declare_blocker(
        self,
        defending_player_index: int,
        blocker_object_id: GameObjectId,
        attacker_object_id: GameObjectId,
    ) -> None:
        """Enregistre un bloqueur sur un attaquant déclaré."""
        self._assert_combat_declarations_allowed()
        if attacker_object_id not in self._declared_attackers:
            msg = "L'attaquant doit être déclaré."
            raise InvalidGameStateError(msg, field_name="attacker_object_id")
        for _b, existing_a in self._declared_blocks:
            if existing_a == attacker_object_id:
                msg = "Un bloqueur est déjà assigné à cet attaquant."
                raise InvalidGameStateError(msg, field_name="attacker_object_id")
        bloc_loc = self.find_location(blocker_object_id)
        if (
            bloc_loc.zone_type is not ZoneType.BATTLEFIELD
            or bloc_loc.player_index != defending_player_index
        ):
            msg = "Le bloqueur doit être sur le champ du défenseur."
            raise InvalidGameStateError(msg, field_name="blocker_object_id")
        bobj = self.get_object(blocker_object_id)
        if not isinstance(bobj, Permanent):
            msg = "Seul un permanent peut bloquer."
            raise InvalidGameStateError(msg, field_name="blocker_object_id")
        for b, _ in self._declared_blocks:
            if b == blocker_object_id:
                msg = "Ce bloqueur est déjà assigné."
                raise InvalidGameStateError(msg, field_name="blocker_object_id")
        self._declared_blocks.append((blocker_object_id, attacker_object_id))
        self.record_engine_event(
            EventType.BLOCKER_DECLARED,
            (
                ("blocker_id", blocker_object_id.value),
                ("attacker_id", attacker_object_id.value),
            ),
        )

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

    def turn_engine_reset_non_empty_stack_passes(self) -> None:
        """Remet à zéro le compteur de passes consécutives lorsque la pile n'est pas vide."""
        self._consecutive_non_empty_stack_passes = 0

    def turn_engine_increment_non_empty_stack_passes(self) -> int:
        """Incrémente les passes consécutives à pile non vide ; retourne la nouvelle valeur."""
        self._consecutive_non_empty_stack_passes += 1
        return self._consecutive_non_empty_stack_passes

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
