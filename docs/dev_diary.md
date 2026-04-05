# Journal de développement — baobab-mtg-rules-engine

Les entrées les plus récentes en premier.

## 2026-04-05 (fin de journée)

### Modifications

- Création de la branche `feature/00-project-bootstrap` et du socle Python (`pyproject.toml`, layout `src/`, `tests/`, `docs/`)
- Implémentation des exceptions racine et techniques initiales avec tests miroir
- Ajout de `README.md`, `CHANGELOG.md`, configuration coverage vers `docs/tests/coverage/`
- Documentation du pipeline de vérification locale dans le README
- Vérifications exécutées : `black`, `flake8`, `mypy`, `pylint`, `bandit`, `pytest` (couverture 100 % sur le package), `python -m build` (sdist + wheel OK)

### Buts

- Satisfaire la feature `00_project_bootstrap` : packagage, qualité, exceptions, documentation minimale
- Préparer le terrain pour les features métier sans introduire de logique de règles

### Impact

- Installation editable et wheel possibles dès la v0.1.0
- Les consommateurs peuvent importer une API publique stable limitée aux exceptions et à `__version__`
- Les garde-fous qualité sont reproductibles via `pyproject.toml`

### Note PR / merge

- À créer côté hébergeur Git : PR `feature/00-project-bootstrap` → `main` après revue ; merge à faire une fois la CI locale (commandes README) au vert.

## 2026-04-05 (démarrage)

### Modifications

- Analyse du dépôt existant (documentation `docs/features`, contraintes `docs/000_dev_constraints.md`)

### Buts

- Cadrer le périmètre strict de la feature 00 et les contraintes transverses (OO, typage, tests, couverture)

### Impact

- Alignement des choix (exceptions explicites, déterminisme, refus net du non supporté) avec la vision moteur
