"""Tests pour :class:`CastSpellAction`."""

from baobab_mtg_rules_engine.actions.cast_spell_action import CastSpellAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


class TestCastSpellAction:
    """Tri par identifiant de carte en main."""

    def test_kind_and_sort_key(self) -> None:
        """Le tri suit l'identifiant du sort en main puis les cibles."""
        cast = CastSpellAction(GameObjectId(3))
        assert cast.kind is SupportedActionKind.CAST_SPELL
        sk = cast.sort_key()
        assert sk[0] == SupportedActionKind.CAST_SPELL.value
        assert sk[1] == 3
        assert not sk[2]
