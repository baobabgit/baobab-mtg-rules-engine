"""Tests unitaires pour :class:`ValidationException`."""

import pytest

from baobab_mtg_rules_engine.exceptions.baobab_mtg_rules_engine_exception import (
    BaobabMtgRulesEngineException,
)
from baobab_mtg_rules_engine.exceptions.validation_exception import ValidationException


class TestValidationException:
    """Vérifie les erreurs de validation explicites."""

    def test_field_name_keyword_only(self) -> None:
        """Le nom de champ est un argument mot-clé optionnel."""
        exc = ValidationException("illégal")
        assert exc.field_name is None

        exc_field = ValidationException("illégal", field_name="zone")
        assert exc_field.field_name == "zone"
        assert exc_field.message == "illégal"

    def test_inherits_engine_base(self) -> None:
        """L'exception hérite de la racine moteur."""
        exc = ValidationException("x")
        assert isinstance(exc, BaobabMtgRulesEngineException)

    def test_raise_for_invalid_action(self) -> None:
        """Scénario type : validation refusée avant mutation."""
        with pytest.raises(ValidationException) as caught:
            raise ValidationException("action interdite", field_name="priority")
        assert caught.value.field_name == "priority"
