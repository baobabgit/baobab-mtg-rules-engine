"""Tests d'import et de métadonnées publiques du package."""

import importlib
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

import pytest

import baobab_mtg_rules_engine as engine_pkg
from baobab_mtg_rules_engine import exceptions as exceptions_pkg


class TestPackagePublicApi:
    """Contrôle la surface publique exposée par ``baobab_mtg_rules_engine``."""

    def test_import_public_exceptions_and_version(self) -> None:
        """Les symboles publics sont importables depuis le package racine."""
        assert hasattr(engine_pkg, "__version__")
        assert isinstance(engine_pkg.__version__, str)
        assert engine_pkg.__version__  # non vide une fois le package installé

        assert hasattr(engine_pkg, "BaobabMtgRulesEngineException")
        assert hasattr(engine_pkg, "InvalidGameStateError")
        assert hasattr(engine_pkg, "UnsupportedRuleException")
        assert hasattr(engine_pkg, "ValidationException")

    def test_all_matches_exported_names(self) -> None:
        """``__all__`` reste cohérent avec les attributs réellement exportés."""
        for name in engine_pkg.__all__:
            assert hasattr(engine_pkg, name)

    def test_reload_preserves_public_api(self) -> None:
        """Un rechargement du module conserve les exports attendus."""
        reloaded = importlib.reload(engine_pkg)
        assert "BaobabMtgRulesEngineException" in reloaded.__all__

    def test_version_fallback_when_distribution_missing(self) -> None:
        """Si les métadonnées du wheel ne sont pas trouvées, la version retombe sur 0.0.0."""
        with patch(
            "importlib.metadata.version",
            side_effect=PackageNotFoundError(),
        ):
            reloaded = importlib.reload(engine_pkg)
            assert reloaded.__version__ == "0.0.0"
        importlib.reload(engine_pkg)

    @pytest.mark.parametrize(
        "name",
        [
            "BaobabMtgRulesEngineException",
            "InvalidGameStateError",
            "UnsupportedRuleException",
            "ValidationException",
        ],
    )
    def test_exceptions_exported_via_exceptions_subpackage(self, name: str) -> None:
        """Le sous-paquet ``exceptions`` ré-exporte les mêmes types publics."""
        assert hasattr(exceptions_pkg, name)
