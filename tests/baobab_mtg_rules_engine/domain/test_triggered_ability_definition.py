"""Tests pour :class:`TriggeredAbilityDefinition`."""

import pytest

from baobab_mtg_rules_engine.domain.triggered_ability_definition import TriggeredAbilityDefinition


class TestTriggeredAbilityDefinition:
    """Validation du contrat de définition des triggers."""

    def test_valid_begin_step_definition(self) -> None:
        """Une définition begin_step complète est acceptée."""
        definition = TriggeredAbilityDefinition(
            ability_key="k",
            trigger_kind="begin_step",
            trigger_step="UPKEEP",
            trigger_step_scope="you",
            effect_kind="damage_opponent",
            amount=1,
        )
        assert definition.trigger_kind == "begin_step"
        assert definition.trigger_step == "UPKEEP"

    def test_valid_non_step_definition(self) -> None:
        """Une définition non begin_step ne requiert pas trigger_step."""
        definition = TriggeredAbilityDefinition(
            ability_key="k2",
            trigger_kind="cast_self",
            effect_kind="draw_cards",
            amount=1,
        )
        assert definition.trigger_step is None

    def test_empty_ability_key_raises(self) -> None:
        """La clé logique ne peut pas être vide."""
        with pytest.raises(ValueError, match="ability_key"):
            TriggeredAbilityDefinition(
                ability_key="",
                trigger_kind="cast_self",
                effect_kind="damage_opponent",
            )

    def test_unknown_trigger_kind_raises(self) -> None:
        """Le type de trigger doit appartenir au périmètre supporté."""
        with pytest.raises(ValueError, match="trigger_kind"):
            TriggeredAbilityDefinition(
                ability_key="k",
                trigger_kind="unknown",
                effect_kind="damage_opponent",
            )

    def test_unknown_effect_kind_raises(self) -> None:
        """Le type d'effet doit appartenir au périmètre supporté."""
        with pytest.raises(ValueError, match="effect_kind"):
            TriggeredAbilityDefinition(
                ability_key="k",
                trigger_kind="cast_self",
                effect_kind="unknown",
            )

    def test_negative_amount_raises(self) -> None:
        """Le montant d'effet ne peut pas être négatif."""
        with pytest.raises(ValueError, match="amount"):
            TriggeredAbilityDefinition(
                ability_key="k",
                trigger_kind="cast_self",
                effect_kind="damage_opponent",
                amount=-1,
            )

    def test_unknown_target_kind_raises(self) -> None:
        """Le type de cible doit être none/player/creature."""
        with pytest.raises(ValueError, match="target_kind"):
            TriggeredAbilityDefinition(
                ability_key="k",
                trigger_kind="cast_self",
                effect_kind="damage_player",
                target_kind="planeswalker",
            )

    def test_begin_step_without_step_raises(self) -> None:
        """Un trigger begin_step doit préciser trigger_step."""
        with pytest.raises(ValueError, match="trigger_step"):
            TriggeredAbilityDefinition(
                ability_key="k",
                trigger_kind="begin_step",
                effect_kind="damage_opponent",
            )

    def test_begin_step_with_invalid_scope_raises(self) -> None:
        """Le scope de begin_step doit être you ou any."""
        with pytest.raises(ValueError, match="trigger_step_scope"):
            TriggeredAbilityDefinition(
                ability_key="k",
                trigger_kind="begin_step",
                trigger_step="UPKEEP",
                trigger_step_scope="opponent",
                effect_kind="damage_opponent",
            )

    def test_non_begin_step_with_trigger_step_raises(self) -> None:
        """trigger_step est interdit pour les autres trigger_kind."""
        with pytest.raises(ValueError, match="trigger_step"):
            TriggeredAbilityDefinition(
                ability_key="k",
                trigger_kind="cast_self",
                trigger_step="UPKEEP",
                effect_kind="damage_opponent",
            )
