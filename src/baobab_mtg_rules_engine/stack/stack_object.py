"""Métadonnées d'un sort (ou objet) sur la pile."""

from __future__ import annotations

from dataclasses import dataclass

from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId
from baobab_mtg_rules_engine.targeting.simple_target import SimpleTarget


@dataclass(frozen=True, slots=True)
class StackObject:
    """Vue opérationnelle d'un sort sur la pile : contrôleur, clé catalogue et cibles.

    L'identifiant ``spell_object_id`` désigne l'instance
    :class:`~baobab_mtg_rules_engine.domain.spell_on_stack.SpellOnStack` présente dans la
    zone pile.
    """

    spell_object_id: GameObjectId
    controller_player_index: int
    catalog_key: str
    targets: tuple[SimpleTarget, ...]
