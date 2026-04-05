"""Tests unitaires pour :class:`BaobabMtgRulesEngineException`."""

import pytest

from baobab_mtg_rules_engine.exceptions.baobab_mtg_rules_engine_exception import (
    BaobabMtgRulesEngineException,
)


class TestBaobabMtgRulesEngineException:
    """Vérifie le comportement de l'exception racine du moteur."""

    def test_message_property_returns_constructor_value(self) -> None:
        """Le message exposé correspond à celui passé au constructeur."""
        exc = BaobabMtgRulesEngineException("erreur-test")
        assert exc.message == "erreur-test"
        assert str(exc) == "erreur-test"

    def test_is_catchable_as_exception(self) -> None:
        """L'exception reste une :class:`Exception` standard."""
        with pytest.raises(BaobabMtgRulesEngineException) as caught:
            raise BaobabMtgRulesEngineException("boom")
        assert caught.value.message == "boom"
