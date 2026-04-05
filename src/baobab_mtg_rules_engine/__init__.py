"""API publique du package ``baobab_mtg_rules_engine``.

Ce module expose la version du distribution package et les exceptions
stables destinées aux consommateurs de la bibliothèque.
"""

from importlib.metadata import PackageNotFoundError, version

from baobab_mtg_rules_engine.exceptions import (
    BaobabMtgRulesEngineException,
    IllegalGameActionError,
    InvalidGameStateError,
    UnsupportedRuleException,
    ValidationException,
)

try:
    __version__: str = version("baobab-mtg-rules-engine")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "BaobabMtgRulesEngineException",
    "IllegalGameActionError",
    "InvalidGameStateError",
    "UnsupportedRuleException",
    "ValidationException",
]
