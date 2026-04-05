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

Toute erreur spécifique au moteur dérive de `BaobabMtgRulesEngineException` (également exportée depuis le package racine). Les erreurs de cohérence du domaine partie utilisent `InvalidGameStateError`.

## Modèle de domaine (aperçu)

Le sous-paquet `baobab_mtg_rules_engine.domain` expose les entités et value objects centraux : état à deux joueurs, zones, tour (`Phase` / `Step`), identifiants d’objets stables et distinction **référence de carte** (`CardReference`) vs **objet en partie** (`InGameCard` et sous-classes).

```python
from baobab_mtg_rules_engine.domain import (
    CardReference,
    Game,
    GameState,
    Permanent,
    SpellOnStack,
    ZoneLocation,
    ZoneType,
)

game = Game.create_two_player("demo")
state = game.state
card_id = state.issue_object_id()
spell = SpellOnStack(card_id, CardReference("oracle:12345"))
state.register_object_at(spell, ZoneLocation(None, ZoneType.STACK))
new_id = state.migrate_in_game_card_as_new_instance(
    card_id,
    target=ZoneLocation(0, ZoneType.BATTLEFIELD),
    new_kind=Permanent,
)
assert new_id != card_id
```

Les déplacements peuvent soit **conserver** l’identifiant (`relocate_preserving_identity`), soit créer une **nouvelle instance logique** avec un nouvel identifiant (`migrate_in_game_card_as_new_instance`).

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
