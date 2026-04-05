"""Tests pour :class:`PlayLandAction`."""

from baobab_mtg_rules_engine.actions.play_land_action import PlayLandAction
from baobab_mtg_rules_engine.actions.supported_action_kind import SupportedActionKind
from baobab_mtg_rules_engine.domain.game_object_id import GameObjectId


class TestPlayLandAction:
    """Tri déterministe par identifiant d'objet."""

    def test_kind_and_sort_key(self) -> None:
        """Le tri suit l'identifiant de la carte en main."""
        land = PlayLandAction(GameObjectId(5))
        assert land.kind is SupportedActionKind.PLAY_LAND
        assert land.sort_key() == (SupportedActionKind.PLAY_LAND.value, 5)
