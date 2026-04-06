"""Tests pour :class:`InvalidSpellTargetError`."""

import pytest

from baobab_mtg_rules_engine.exceptions.invalid_spell_target_error import InvalidSpellTargetError
from baobab_mtg_rules_engine.exceptions.validation_exception import ValidationException


class TestInvalidSpellTargetError:
    """Héritage validation."""

    def test_is_validation_subclass(self) -> None:
        """Erreur métier de validation."""
        err = InvalidSpellTargetError("x", field_name="targets")
        assert isinstance(err, ValidationException)

    def test_can_raise(self) -> None:
        """Capturable comme :class:`ValidationException`."""
        with pytest.raises(ValidationException):
            raise InvalidSpellTargetError("bad", field_name="t")
