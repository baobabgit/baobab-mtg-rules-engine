# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format s’inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [0.1.0] - 2026-04-05

### Added

- Squelette du package `baobab_mtg_rules_engine` (layout `src/`)
- Hiérarchie d’exceptions : `BaobabMtgRulesEngineException`, `UnsupportedRuleException`, `ValidationException`
- Configuration centralisée des outils qualité dans `pyproject.toml` (black, flake8, mypy, pylint, bandit, pytest, coverage)
- Documentation minimale : `README.md`, journal `docs/dev_diary.md`, répertoire de rapports de couverture `docs/tests/coverage/`
- Tests unitaires de base et seuil de couverture à 90 %
