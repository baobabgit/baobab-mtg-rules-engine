# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format s’inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [0.2.0] - 2026-04-05

### Added

- Module `baobab_mtg_rules_engine.domain` : `Game`, `GameState`, `PlayerState`, `Zone`, `TurnState`, énumérations `ZoneType`, `Phase`, `Step`
- Objets de jeu : `GameObjectId`, `CardReference`, `InGameCard`, `Permanent`, `SpellOnStack`, `AbilityOnStack`
- Journal minimal : `GameEvent`, `EventType` ; protocoles d’extension `AbilityLike`, `EffectLike`
- Exception `InvalidGameStateError` pour les violations d’invariants de partie
- Tests unitaires miroir sous `tests/baobab_mtg_rules_engine/domain/`

## [0.1.0] - 2026-04-05

### Added

- Squelette du package `baobab_mtg_rules_engine` (layout `src/`)
- Hiérarchie d’exceptions : `BaobabMtgRulesEngineException`, `UnsupportedRuleException`, `ValidationException`
- Configuration centralisée des outils qualité dans `pyproject.toml` (black, flake8, mypy, pylint, bandit, pytest, coverage)
- Documentation minimale : `README.md`, journal `docs/dev_diary.md`, répertoire de rapports de couverture `docs/tests/coverage/`
- Tests unitaires de base et seuil de couverture à 90 %
