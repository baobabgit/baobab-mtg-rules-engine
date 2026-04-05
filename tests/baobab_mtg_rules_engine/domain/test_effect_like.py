"""Tests pour le protocole :class:`EffectLike`."""

from baobab_mtg_rules_engine.domain.effect_like import EffectLike


class _StubEffect:
    """Implémentation minimale pour vérification structurelle."""

    @property
    def effect_key(self) -> str:
        """Clé factice pour satisfaire :class:`EffectLike`."""
        return "stub-effect"


class TestEffectLike:
    """Point d'extension effets."""

    def test_runtime_checkable(self) -> None:
        """Un objet portant ``effect_key`` satisfait le protocole."""
        assert isinstance(_StubEffect(), EffectLike)
