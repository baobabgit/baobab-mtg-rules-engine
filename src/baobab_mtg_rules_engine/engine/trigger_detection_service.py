"""Détection des capacités déclenchées à partir du journal d'événements."""

# Le routeur d'événements reçoit explicitement le contexte complet de l'événement.
# pylint: disable=too-many-positional-arguments

from __future__ import annotations

from baobab_mtg_rules_engine.catalog.card_gameplay_port import CardGameplayPort
from baobab_mtg_rules_engine.domain.event_type import EventType
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.domain.game_state import GameState
from baobab_mtg_rules_engine.domain.in_game_card import InGameCard
from baobab_mtg_rules_engine.domain.pending_triggered_ability import PendingTriggeredAbility
from baobab_mtg_rules_engine.domain.triggered_ability_definition import TriggeredAbilityDefinition
from baobab_mtg_rules_engine.domain.zone_type import ZoneType
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError


class TriggerDetectionService:
    """Traduit les événements de partie en triggers en attente."""

    _IGNORED_EVENT_TYPES: frozenset[EventType] = frozenset(
        {
            EventType.TRIGGER_DETECTED,
            EventType.TRIGGER_QUEUED,
            EventType.TRIGGER_STACKED,
            EventType.TRIGGER_RESOLVED,
            EventType.TRIGGER_FIZZLED,
        }
    )
    _PLAYER_INDICES: tuple[int, int] = (0, 1)

    def scan_new_events(
        self,
        state: GameState,
        rules: CardGameplayPort,
        *,
        from_sequence_exclusive: int,
    ) -> int:
        """Détecte les triggers pour les événements non encore inspectés.

        :return: Dernier numéro de séquence traité.
        """
        new_events = tuple(
            event for event in state.events if event.sequence > from_sequence_exclusive
        )
        if not new_events:
            return from_sequence_exclusive
        max_seen = new_events[-1].sequence
        for event in new_events:
            if event.event_type in self._IGNORED_EVENT_TYPES:
                continue
            self._detect_from_event(state, rules, event.event_type, event.sequence, event.payload)
        return max_seen

    def detect_begin_step_from_state(
        self,
        state: GameState,
        rules: CardGameplayPort,
    ) -> None:
        """Détecte les triggers ``begin_step`` depuis l'état courant.

        Cette voie est utilisée lorsque le scan incrémental démarre après que
        l'événement ``TURN_STEP_ENTERED`` de l'étape ait déjà été émis.
        """
        step = state.turn_state.step.name
        active_player = state.turn_state.active_player_index
        self._detect_begin_step_for_context(
            state, rules, event_sequence=-1, step=step, active_player=active_player
        )

    def _detect_from_event(
        self,
        state: GameState,
        rules: CardGameplayPort,
        event_type: EventType,
        event_sequence: int,
        payload: tuple[tuple[str, str | int], ...],
    ) -> None:
        data = dict(payload)
        if event_type is EventType.OBJECT_RELOCATED:
            self._detect_etb_and_dies_from_relocated(state, rules, event_sequence, data)
            return
        if event_type is EventType.OBJECT_REPLACED_BY_NEW_IDENTITY:
            self._detect_etb_from_replaced_identity(state, rules, event_sequence, data)
            return
        if event_type is EventType.SPELL_CAST:
            self._detect_cast_self(state, rules, event_sequence, data)
            return
        if event_type is EventType.TURN_STEP_ENTERED:
            self._detect_begin_step(state, rules, event_sequence, data)
            return
        if event_type is EventType.TURN_DRAW_PERFORMED:
            self._detect_draw(state, rules, event_sequence, data)
            return
        if event_type is EventType.COMBAT_DAMAGE_ASSIGNED:
            self._detect_combat_damage_to_player(state, rules, event_sequence, data)
            return

    def _detect_etb_and_dies_from_relocated(
        self,
        state: GameState,
        rules: CardGameplayPort,
        event_sequence: int,
        data: dict[str, str | int],
    ) -> None:
        object_id = self._extract_object_id(data, "object_id")
        if object_id is None:
            return
        from_zone = self._extract_str(data, "from_zone")
        to_zone = self._extract_str(data, "to_zone")
        to_player = self._extract_player_index(data, "to_player")
        from_player = self._extract_player_index(data, "from_player")
        if to_zone == ZoneType.BATTLEFIELD.name and to_player is not None:
            self._enqueue_self_triggers(
                state,
                rules,
                source_object_id=object_id,
                event_sequence=event_sequence,
                trigger_kind="etb_self",
                forced_controller=to_player,
            )
        if (
            from_zone == ZoneType.BATTLEFIELD.name
            and to_zone == ZoneType.GRAVEYARD.name
            and from_player is not None
        ):
            self._enqueue_self_triggers(
                state,
                rules,
                source_object_id=object_id,
                event_sequence=event_sequence,
                trigger_kind="dies_self",
                forced_controller=from_player,
            )

    def _detect_etb_from_replaced_identity(
        self,
        state: GameState,
        rules: CardGameplayPort,
        event_sequence: int,
        data: dict[str, str | int],
    ) -> None:
        to_zone = self._extract_str(data, "to_zone")
        to_player = self._extract_player_index(data, "to_player")
        new_object_id = self._extract_object_id(data, "new_object_id")
        if (
            to_zone == ZoneType.BATTLEFIELD.name
            and to_player is not None
            and new_object_id is not None
        ):
            self._enqueue_self_triggers(
                state,
                rules,
                source_object_id=new_object_id,
                event_sequence=event_sequence,
                trigger_kind="etb_self",
                forced_controller=to_player,
            )

    def _detect_cast_self(
        self,
        state: GameState,
        rules: CardGameplayPort,
        event_sequence: int,
        data: dict[str, str | int],
    ) -> None:
        stack_object_id = self._extract_object_id(data, "new_object_id")
        controller = self._extract_player_index(data, "player_index")
        if stack_object_id is None or controller is None:
            return
        self._enqueue_self_triggers(
            state,
            rules,
            source_object_id=stack_object_id,
            event_sequence=event_sequence,
            trigger_kind="cast_self",
            forced_controller=controller,
        )

    def _detect_begin_step(
        self,
        state: GameState,
        rules: CardGameplayPort,
        event_sequence: int,
        data: dict[str, str | int],
    ) -> None:
        step = self._extract_str(data, "step")
        active_player = self._extract_player_index(data, "active_player")
        if step is None or active_player is None:
            return
        self._detect_begin_step_for_context(
            state,
            rules,
            event_sequence=event_sequence,
            step=step,
            active_player=active_player,
        )

    def _detect_begin_step_for_context(
        self,
        state: GameState,
        rules: CardGameplayPort,
        *,
        event_sequence: int,
        step: str,
        active_player: int,
    ) -> None:
        for controller in self._PLAYER_INDICES:
            for source_id in state.players[controller].zone(ZoneType.BATTLEFIELD).object_ids():
                for definition in self._definitions_for_source(state, rules, source_id):
                    if definition.trigger_kind != "begin_step":
                        continue
                    if definition.trigger_step != step:
                        continue
                    if definition.trigger_step_scope == "you" and active_player != controller:
                        continue
                    self._queue_trigger(
                        state,
                        source_object_id=source_id,
                        controller_player_index=controller,
                        definition=definition,
                        trigger_event_sequence=event_sequence,
                    )

    def _detect_draw(
        self,
        state: GameState,
        rules: CardGameplayPort,
        event_sequence: int,
        data: dict[str, str | int],
    ) -> None:
        drawer = self._extract_player_index(data, "player_index")
        if drawer is None:
            return
        for source_id in state.players[drawer].zone(ZoneType.BATTLEFIELD).object_ids():
            for definition in self._definitions_for_source(state, rules, source_id):
                if definition.trigger_kind == "draw_you":
                    self._queue_trigger(
                        state,
                        source_object_id=source_id,
                        controller_player_index=drawer,
                        definition=definition,
                        trigger_event_sequence=event_sequence,
                    )

    def _detect_combat_damage_to_player(
        self,
        state: GameState,
        rules: CardGameplayPort,
        event_sequence: int,
        data: dict[str, str | int],
    ) -> None:
        target = self._extract_str(data, "target")
        if target != "player":
            return
        attacker_id = self._extract_object_id(data, "attacker_id")
        if attacker_id is None:
            return
        controller = self._controller_from_location(state, attacker_id)
        if controller is None:
            return
        self._enqueue_self_triggers(
            state,
            rules,
            source_object_id=attacker_id,
            event_sequence=event_sequence,
            trigger_kind="combat_damage_to_player_self",
            forced_controller=controller,
        )

    def _enqueue_self_triggers(
        self,
        state: GameState,
        rules: CardGameplayPort,
        *,
        source_object_id: GameObjectId,
        event_sequence: int,
        trigger_kind: str,
        forced_controller: int,
    ) -> None:
        for definition in self._definitions_for_source(state, rules, source_object_id):
            if definition.trigger_kind != trigger_kind:
                continue
            self._queue_trigger(
                state,
                source_object_id=source_object_id,
                controller_player_index=forced_controller,
                definition=definition,
                trigger_event_sequence=event_sequence,
            )

    def _definitions_for_source(
        self,
        state: GameState,
        rules: CardGameplayPort,
        source_object_id: GameObjectId,
    ) -> tuple[TriggeredAbilityDefinition, ...]:
        try:
            source = state.get_object(source_object_id)
        except InvalidGameStateError:
            return ()
        if not isinstance(source, InGameCard):
            return ()
        return rules.triggered_ability_definitions(source.card_reference.catalog_key)

    def _queue_trigger(
        self,
        state: GameState,
        *,
        source_object_id: GameObjectId,
        controller_player_index: int,
        definition: TriggeredAbilityDefinition,
        trigger_event_sequence: int,
    ) -> None:
        source_catalog_key = self._source_catalog_key(state, source_object_id)
        pending = PendingTriggeredAbility(
            pending_trigger_id=state.issue_pending_trigger_id(),
            controller_player_index=controller_player_index,
            source_object_id=source_object_id,
            source_catalog_key=source_catalog_key,
            ability_definition=definition,
            trigger_event_sequence=trigger_event_sequence,
        )
        state.record_engine_event(
            EventType.TRIGGER_DETECTED,
            (
                ("pending_trigger_id", pending.pending_trigger_id),
                ("controller_player_index", controller_player_index),
                ("source_object_id", source_object_id.value),
                ("ability_key", definition.ability_key),
                ("trigger_kind", definition.trigger_kind),
                ("event_sequence", trigger_event_sequence),
            ),
        )
        state.queue_pending_trigger(pending)
        state.record_engine_event(
            EventType.TRIGGER_QUEUED,
            (
                ("pending_trigger_id", pending.pending_trigger_id),
                ("controller_player_index", controller_player_index),
                ("source_object_id", source_object_id.value),
                ("ability_key", definition.ability_key),
            ),
        )

    def _source_catalog_key(self, state: GameState, source_object_id: GameObjectId) -> str:
        try:
            source = state.get_object(source_object_id)
        except InvalidGameStateError:
            return ""
        if not isinstance(source, InGameCard):
            return ""
        return source.card_reference.catalog_key

    def _controller_from_location(self, state: GameState, object_id: GameObjectId) -> int | None:
        try:
            loc = state.find_location(object_id)
        except InvalidGameStateError:
            return None
        return loc.player_index

    def _extract_str(self, data: dict[str, str | int], key: str) -> str | None:
        value = data.get(key)
        if isinstance(value, str):
            return value
        return None

    def _extract_object_id(self, data: dict[str, str | int], key: str) -> GameObjectId | None:
        value = data.get(key)
        if isinstance(value, int) and value >= 1:
            return GameObjectId(value)
        return None

    def _extract_player_index(self, data: dict[str, str | int], key: str) -> int | None:
        value = data.get(key)
        if isinstance(value, int) and value in (0, 1):
            return value
        return None
