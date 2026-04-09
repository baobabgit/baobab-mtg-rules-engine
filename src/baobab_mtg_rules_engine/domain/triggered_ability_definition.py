"""Définition déclarative d'une capacité déclenchée supportée par le noyau."""

from __future__ import annotations

from dataclasses import dataclass


_SUPPORTED_TRIGGER_KINDS: frozenset[str] = frozenset(
    {
        "etb_self",
        "dies_self",
        "cast_self",
        "begin_step",
        "draw_you",
        "combat_damage_to_player_self",
    }
)
_SUPPORTED_STEP_SCOPES: frozenset[str] = frozenset({"you", "any"})
_SUPPORTED_TARGET_KINDS: frozenset[str] = frozenset({"none", "player", "creature"})
_SUPPORTED_EFFECT_KINDS: frozenset[str] = frozenset(
    {"damage_opponent", "damage_player", "destroy_target_creature", "draw_cards"}
)


@dataclass(frozen=True, slots=True)
class TriggeredAbilityDefinition:
    """Capacité déclenchée sérialisable injectée via le catalogue gameplay.

    Le moteur supporte un sous-ensemble déterministe de profils :
    - déclencheurs ``etb_self``, ``dies_self``, ``cast_self``, ``begin_step``,
      ``draw_you`` et ``combat_damage_to_player_self`` ;
    - cibles ``none``, ``player`` ou ``creature`` ;
    - effets simples ``damage_opponent``, ``damage_player``,
      ``destroy_target_creature`` et ``draw_cards``.
    """

    ability_key: str
    trigger_kind: str
    effect_kind: str
    amount: int = 1
    target_kind: str = "none"
    trigger_step: str | None = None
    trigger_step_scope: str = "you"

    def __post_init__(self) -> None:
        if not self.ability_key:
            msg = "ability_key ne peut pas être vide."
            raise ValueError(msg)
        if self.trigger_kind not in _SUPPORTED_TRIGGER_KINDS:
            msg = f"trigger_kind non supporté: {self.trigger_kind!r}."
            raise ValueError(msg)
        if self.effect_kind not in _SUPPORTED_EFFECT_KINDS:
            msg = f"effect_kind non supporté: {self.effect_kind!r}."
            raise ValueError(msg)
        if self.amount < 0:
            msg = "amount ne peut pas être négatif."
            raise ValueError(msg)
        if self.target_kind not in _SUPPORTED_TARGET_KINDS:
            msg = f"target_kind non supporté: {self.target_kind!r}."
            raise ValueError(msg)
        if self.trigger_kind == "begin_step":
            if self.trigger_step is None or self.trigger_step == "":
                msg = "trigger_step est requis pour trigger_kind='begin_step'."
                raise ValueError(msg)
            if self.trigger_step_scope not in _SUPPORTED_STEP_SCOPES:
                msg = f"trigger_step_scope non supporté: {self.trigger_step_scope!r}."
                raise ValueError(msg)
        elif self.trigger_step is not None:
            msg = "trigger_step ne peut être défini que pour trigger_kind='begin_step'."
            raise ValueError(msg)
