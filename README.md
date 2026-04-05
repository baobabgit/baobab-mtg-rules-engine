# baobab-mtg-rules-engine

Bibliothèque Python pour un **moteur de règles Magic: The Gathering** orienté **déterminisme**, **inspectabilité** et **validation explicite** des actions. Le projet s’inscrit dans l’écosystème Baobab MTG.

## Prérequis

- Python **3.11** ou supérieur
- Un environnement virtuel recommandé

## Installation (développement)

```bash
python -m pip install -e ".[dev]"
```

Construction d’une roue (wheel) :

```bash
python -m pip install build
python -m build
```

Les artefacts sont produits sous `dist/`.

## Utilisation minimale

```python
from baobab_mtg_rules_engine import (
    UnsupportedRuleException,
    ValidationException,
    __version__,
)

print(__version__)

raise UnsupportedRuleException("Fonctionnalité non encore implémentée", rule_reference="XXX")
```

Toute erreur spécifique au moteur dérive de `BaobabMtgRulesEngineException` (également exportée depuis le package racine).

## Vérification qualité (pipeline local)

Après `pip install -e ".[dev]"`, exécuter dans l’ordre :

```bash
python -m black --check .
python -m flake8 .
python -m mypy src tests
python -m pylint src tests
python -m bandit -r src
python -m pytest --cov=src/baobab_mtg_rules_engine --cov-report=term-missing
```

Les rapports de couverture HTML et XML sont générés sous `docs/tests/coverage/` (voir `docs/tests/coverage/README.md`). Le seuil minimal de couverture est défini dans `pyproject.toml` (**90 %**).

## Documentation

- Contraintes de développement : `docs/000_dev_constraints.md`
- Spécifications : `docs/001_specifications.md`
- Journal de développement : `docs/dev_diary.md`
- Historique des versions : `CHANGELOG.md`

## Contribution

- Branches de fonctionnalité : `feature/<nom>`
- Commits : [Conventional Commits](https://www.conventionalcommits.org/)
- Tests et outils de qualité doivent passer avant fusion sur `main`

## Licence

Voir la métadonnée `license` dans `pyproject.toml` et les conventions du dépôt Baobab.
