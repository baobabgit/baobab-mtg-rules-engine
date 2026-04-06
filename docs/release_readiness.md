# Release readiness — baobab-mtg-rules-engine

Ce document résume les prérequis et vérifications avant publication publique d’une distribution (wheel / sdist).

## Prérequis

- Python **3.11+** (3.11 et 3.12 couverts par la CI GitHub Actions).
- Compte et droits pour publier sur l’index PyPI cible (si publication officielle).
- Dépôt aligné sur `main` ; la CI ne s’exécute qu’au **tag** (voir ci-dessous).

## Vérifications locales (ordre recommandé)

```bash
python -m pip install -e ".[dev]"
python -m black --check .
python -m flake8 .
python -m mypy src tests
python -m pylint src tests
python -m bandit -r src
python -m pytest --cov=src/baobab_mtg_rules_engine --cov-report=term-missing
python -m pip install build
python -m build
```

La configuration `pytest` / `coverage` dans `pyproject.toml` impose une couverture **≥ 90 %** sur le paquet `baobab_mtg_rules_engine`.

## Construction des artefacts

- **Wheel** et **sdist** : `python -m build` (artefacts sous `dist/`).
- Le fichier `LICENSE` est inclus dans le sdist via `MANIFEST.in` et référencé dans les métadonnées du projet.

## Critères GO (publication)

- Aucune régression sur les contrôles qualité (black, flake8, mypy, pylint, bandit, pytest + couverture).
- Métadonnées `pyproject.toml` cohérentes (version SemVer, URLs du dépôt `baobabgit/baobab-mtg-rules-engine`, statut de maturité, licence propriétaire).
- `CHANGELOG.md` à jour pour la version publiée.
- Après push d’un tag `vX.Y.Z` pointant vers un commit de `main` : workflow `.github/workflows/ci.yml` au vert puis **GitHub Release** publiée avec wheel et sdist.

## CI distante

Déclenchement **uniquement** sur **push de tag** `v*.*.*`. Le commit étiqueté doit être dans l’historique de `main`. Enchaînement : vérification → **quality** (Python 3.11 et 3.12) → **release** (`python -m build` + création de la release avec pièces jointes `dist/*`).
