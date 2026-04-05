"""Tests pour :class:`IllegalGameActionError`."""

import pytest

from baobab_mtg_rules_engine.exceptions.illegal_game_action_error import IllegalGameActionError
from baobab_mtg_rules_engine.exceptions.validation_exception import ValidationException


class TestIllegalGameActionError:
    """Héritage et message."""

    def test_is_validation_exception_subclass(self) -> None:
        """L'erreur est une exception de validation métier."""
        err = IllegalGameActionError("refus", field_name="action")
        assert isinstance(err, ValidationException)

    def test_message_and_field(self) -> None:
        """Le message et le champ sont conservés."""
        err = IllegalGameActionError("hors périmètre", field_name="spell_object_id")
        assert "hors périmètre" in str(err)
        assert err.field_name == "spell_object_id"

    def test_can_be_raised(self) -> None:
        """Levée capturable comme :class:`ValidationException`."""
        with pytest.raises(ValidationException):
            raise IllegalGameActionError("x", field_name="y")
