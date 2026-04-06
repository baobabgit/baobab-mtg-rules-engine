"""Exceptions du moteur de règles Baobab MTG."""

from baobab_mtg_rules_engine.exceptions.baobab_mtg_rules_engine_exception import (
    BaobabMtgRulesEngineException,
)
from baobab_mtg_rules_engine.exceptions.unsupported_rule_exception import (
    UnsupportedRuleException,
)
from baobab_mtg_rules_engine.exceptions.deck_validation_error import DeckValidationError
from baobab_mtg_rules_engine.exceptions.insufficient_library_error import InsufficientLibraryError
from baobab_mtg_rules_engine.exceptions.illegal_game_action_error import IllegalGameActionError
from baobab_mtg_rules_engine.exceptions.invalid_game_state_error import InvalidGameStateError
from baobab_mtg_rules_engine.exceptions.invalid_spell_target_error import InvalidSpellTargetError
from baobab_mtg_rules_engine.exceptions.validation_exception import ValidationException

__all__ = [
    "BaobabMtgRulesEngineException",
    "DeckValidationError",
    "IllegalGameActionError",
    "InsufficientLibraryError",
    "InvalidGameStateError",
    "InvalidSpellTargetError",
    "UnsupportedRuleException",
    "ValidationException",
]
