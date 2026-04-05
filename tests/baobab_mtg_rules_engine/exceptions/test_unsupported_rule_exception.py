"""Tests unitaires pour :class:`UnsupportedRuleException`."""

import pytest

from baobab_mtg_rules_engine.exceptions.baobab_mtg_rules_engine_exception import (
    BaobabMtgRulesEngineException,
)
from baobab_mtg_rules_engine.exceptions.unsupported_rule_exception import (
    UnsupportedRuleException,
)


class TestUnsupportedRuleException:
    """Vérifie le refus explicite des règles non supportées."""

    def test_inherits_from_base_engine_exception(self) -> None:
        """L'exception spécialise l'exception racine du moteur."""
        exc = UnsupportedRuleException("non supporté")
        assert isinstance(exc, BaobabMtgRulesEngineException)

    def test_rule_reference_optional(self) -> None:
        """La référence de règle est optionnelle et exposée via une propriété."""
        without_ref = UnsupportedRuleException("msg")
        assert without_ref.rule_reference is None
        assert without_ref.message == "msg"

        with_ref = UnsupportedRuleException("msg", "704.5a")
        assert with_ref.rule_reference == "704.5a"

    def test_raise_and_catch(self) -> None:
        """Le type peut être filtré de façon précise dans un ``except``."""
        with pytest.raises(UnsupportedRuleException) as caught:
            raise UnsupportedRuleException("capacité X", "123.45")
        assert caught.value.rule_reference == "123.45"
