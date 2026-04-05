# Contraintes et Bonnes Pratiques de Développement

Ce document définit les contraintes et bonnes pratiques à respecter pour le développement du projet `baobab-nom_du_projet`.

## Table des matières

1. [Structure du projet](#structure-du-projet)
2. [Organisation du code](#organisation-du-code)
3. [Gestion des exceptions](#gestion-des-exceptions)
4. [Tests unitaires](#tests-unitaires)
5. [Qualité du code](#qualité-du-code)
6. [Configuration](#configuration)
7. [Documentation](#documentation)
8. [Journal de développement](#journal-de-développement)
9. [Type hints et annotations](#type-hints-et-annotations)
10. [Versioning sémantique](#versioning-sémantique)
11. [Gestion des dépendances](#gestion-des-dépendances)
12. [Standards de nommage](#standards-de-nommage)
13. [Git workflow](#git-workflow)

---

## Structure du projet

### Arborescence

- **Code source** : Le code source du projet doit être placé dans `src/nom_du_projet`
- **Tests** : Les tests unitaires doivent être placés dans le dossier `tests/`
- **Documentation** : La documentation de développement doit être dans le dossier `docs/`

### Organisation des fichiers

- **Une classe par fichier** : Chaque classe doit être définie dans son propre fichier
- **Arborescence logique** : Les classes doivent être organisées par catégorie et sous-catégorie
  - Exemple : `src/baobab_cli/category/subcategory/class_name.py`
  - Les tests doivent refléter cette structure : `tests/baobab_cli/category/subcategory/test_class_name.py`

---

## Organisation du code

### Programmation orientée objet

- Le projet utilise la **programmation orientée classe**
- Chaque classe doit être dans un fichier dédié
- Les noms de fichiers doivent suivre la convention `snake_case` et correspondre au nom de la classe (en `snake_case`)

### Standards de nommage

- **Classes** : Utiliser `PascalCase` (ex: `DataProcessor`, `FileHandler`)
- **Fonctions et méthodes** : Utiliser `snake_case` (ex: `process_data`, `validate_input`)
- **Constantes** : Utiliser `UPPER_SNAKE_CASE` (ex: `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Variables** : Utiliser `snake_case` (ex: `user_name`, `file_path`)
- **Modules et packages** : Utiliser `snake_case` (ex: `data_processor.py`, `file_handler.py`)
- **Noms explicites** : Les noms doivent être descriptifs et éviter les abréviations non évidentes
- **Cohérence** : Respecter la convention PEP 8 pour tous les identifiants

### Exemple de structure

```
src/baobab_cli/
├── exceptions/
│   ├── __init__.py
│   └── base_exception.py
├── core/
│   ├── __init__.py
│   └── base_handler.py
└── utils/
    ├── __init__.py
    └── file_parser.py
```

---

## Gestion des exceptions

### Exceptions personnalisées

- Toutes les exceptions personnalisées doivent **étendre une classe d'exception de base** créée pour le projet
- Cette classe de base doit être définie dans le module `exceptions`
- Les exceptions doivent être organisées de manière hiérarchique selon leur domaine d'application

### Exemple

```python
# src/baobab_cli/exceptions/base_exception.py
class BaobabException(Exception):
    """Classe de base pour toutes les exceptions du projet."""
    pass

# src/baobab_cli/exceptions/validation_exception.py
class ValidationException(BaobabException):
    """Exception levée lors d'erreurs de validation."""
    pass
```

---

## Tests unitaires

### Organisation

- **Un fichier de tests par classe** : Chaque classe doit avoir son fichier de tests correspondant
- **Nommage** : Les fichiers de tests doivent suivre le pattern `test_<nom_classe>.py`
- **Structure** : L'arborescence des tests doit refléter celle du code source
- **Structure des tests** : Les fichiers de tests unitaires doivent être organisés en **classes de tests**
  - Chaque fichier de test doit contenir une classe de test nommée `Test<NomClasse>`
  - Les méthodes de test doivent être des méthodes de cette classe
  - Les méthodes de test doivent suivre le pattern `test_<nom_test>`

### Classes abstraites

- Si la classe à tester est **abstraite**, il faut créer une **classe concrète** pour les tests
- Cette classe concrète doit être définie dans le fichier de tests

### Couverture de code

- **Exigence minimale** : 90% de couverture de code par les tests unitaires
- La couverture doit être vérifiée à chaque commit/PR
- **Emplacement des fichiers de couverture** : Tous les fichiers concernant la couverture de code (coverage) doivent être placés dans le dossier `docs/tests/coverage`
  - Cela inclut le fichier `.coverage` et tous les rapports générés (HTML, XML, JSON et autres formats)
  - La configuration de coverage doit être ajustée pour générer les fichiers dans ce dossier

### Exemple

```python
# tests/baobab_cli/core/test_base_handler.py
from abc import ABC
from baobab_cli.core.base_handler import BaseHandler

class ConcreteHandler(BaseHandler):  # Pour tester une classe abstraite
    def process(self):
        return "processed"

class TestBaseHandler:
    """Classe de tests pour BaseHandler."""
    
    def test_handler(self):
        """Test du handler."""
        handler = ConcreteHandler()
        assert handler.process() == "processed"
```

---

## Qualité du code

### Outils de vérification

Le code doit passer **tous** les outils suivants sans erreur :

- **black** : Formatage automatique du code
- **pylint** : Analyse statique et détection d'erreurs
- **mypy** : Vérification des types
- **flake8** : Vérification du style PEP 8
- **bandit** : Détection de problèmes de sécurité

### Longueur des lignes

- **Longueur maximale** : 100 caractères par ligne
- Cette limite doit être respectée dans tout le code source et les tests

### Configuration des outils

Tous les outils doivent être configurés dans `pyproject.toml` pour garantir la cohérence entre les environnements de développement.

### Configuration détaillée dans pyproject.toml

Tous les outils de qualité et de développement doivent avoir leur configuration complète dans `pyproject.toml` :

- **black** : Configuration du formatage (longueur de ligne, guillemets, etc.)
- **pylint** : Règles de linting, fichiers à ignorer, scores minimaux
- **mypy** : Configuration de la vérification de types, options strictes
- **flake8** : Règles de style, longueur de ligne, codes d'erreur à ignorer
- **bandit** : Niveaux de sécurité, tests à exécuter
- **pytest** : Configuration des tests, plugins, options d'exécution
- **coverage** : Configuration de la couverture de code, seuils minimaux

Cette centralisation garantit que tous les développeurs utilisent les mêmes règles et configurations.

---

## Configuration

### Fichier pyproject.toml

- **Tous les paramètres** du projet et des tests unitaires doivent être configurés dans `pyproject.toml` (quand c'est possible)
- Cela inclut :
  - Configuration des outils de qualité (black, pylint, mypy, flake8, bandit)
  - Configuration de pytest
  - Configuration de la couverture de code
  - Dépendances du projet
  - Métadonnées du projet

### Gestion des dépendances

- **Séparation des dépendances** : Les dépendances doivent être clairement séparées entre :
  - **Dépendances de production** : Dans `[project.dependencies]`
  - **Dépendances de développement** : Dans `[project.optional-dependencies.dev]`
- **Contraintes de versions** : Utiliser des contraintes de versions précises pour garantir la reproductibilité
  - Format recommandé : `package>=version,<next_major` (ex: `pytest>=7.0.0,<8.0.0`)
  - Éviter `*` ou les versions trop larges sans justification
- **Dépendances optionnelles** : Grouper les dépendances optionnelles par fonctionnalité si nécessaire
- **Mise à jour** : Documenter les raisons des mises à jour de dépendances dans le journal de développement

---

## Documentation

### Docstrings

- Toutes les classes, méthodes et fonctions publiques doivent avoir des **docstrings**
- Format recommandé : **reStructuredText** (format Sphinx)
- Les docstrings doivent décrire :
  - Le but de la classe/fonction
  - Les paramètres (avec types)
  - Les valeurs de retour (avec types)
  - Les exceptions levées
  - Des exemples d'utilisation si pertinent

### Exemple

```python
class DataProcessor:
    """Classe pour traiter les données d'entrée.
    
    Cette classe permet de valider et transformer les données
    selon les règles métier définies.
    
    :param config: Configuration du processeur.
    :type config: dict[str, str]
    :ivar config: Configuration du processeur.
    :type config: dict[str, str]
    
    :Example:
        >>> processor = DataProcessor(config)
        >>> result = processor.process(data)
    """
    pass
```

### Documentation utilisateur

- **README.md** : Le projet doit avoir un fichier `README.md` à la racine contenant :
  - Description du projet
  - Instructions d'installation
  - Guide d'utilisation de base
  - Exemples d'utilisation
  - Informations sur la contribution
  - Licence du projet
- **Documentation API** : Pour les projets complexes, considérer l'utilisation d'outils comme :
  - **Sphinx** : Documentation complète avec génération HTML/PDF
  - **MkDocs** : Documentation moderne avec thèmes personnalisables
- **Exemples** : Fournir des exemples d'utilisation dans la documentation
- **Changelog** : Maintenir un fichier `CHANGELOG.md` pour documenter les changements entre versions

---

## Journal de développement

### Fichier dev_diary.md

- Le journal de développement doit être tenu dans `docs/dev_diary.md`
- **Format des logs** : Classés par **date et heure décroissantes** (les plus récents en premier)

### Contenu de chaque log

Chaque entrée du journal doit indiquer :

1. **Date et heure** : Timestamp de la modification
2. **Modifications** : Description détaillée des changements effectués
3. **Buts** : Objectifs visés par ces modifications
4. **Impact** : Comment ces modifications permettent d'approcher ou d'atteindre le but

### Format d'exemple

```markdown
## 2024-01-15 14:30:00

### Modifications
- Création de la classe `BaseException` dans `exceptions/base_exception.py`
- Ajout des tests unitaires correspondants

### Buts
- Mettre en place une hiérarchie d'exceptions cohérente pour le projet
- Faciliter la gestion d'erreurs centralisée

### Impact
- Toutes les exceptions personnalisées pourront maintenant hériter de `BaobabException`
- Cela permettra de capturer toutes les exceptions du projet de manière uniforme
- Les tests garantissent que la classe fonctionne correctement
```

---

## Type hints et annotations

### Utilisation obligatoire

- **Toutes les fonctions et méthodes** doivent avoir des **annotations de type** pour :
  - Les paramètres
  - Les valeurs de retour
- **Toutes les variables de classe** doivent être annotées avec leur type
- **Les attributs d'instance** doivent être annotés dans la classe ou dans `__init__`

### Types à utiliser

- Utiliser les types de la bibliothèque standard `typing` :
  - `List`, `Dict`, `Tuple`, `Set`, `Optional`, `Union`, etc.
  - Ou les types génériques natifs de Python 3.9+ : `list`, `dict`, `tuple`, `set`
- Utiliser `typing.Protocol` pour les interfaces structurelles
- Utiliser `typing.Generic` pour les classes génériques
- Utiliser `typing.TypeVar` pour les types variables

### Configuration mypy

- La configuration mypy doit être stricte pour garantir la qualité des types
- Utiliser `mypy --strict` ou configurer les options strictes dans `pyproject.toml`
- Tous les fichiers doivent passer la vérification mypy sans erreur

### Exemple

```python
from typing import List, Optional, Dict

class DataProcessor:
    """Processeur de données."""
    
    def __init__(self, config: Dict[str, str]) -> None:
        """Initialise le processeur.
        
        Args:
            config: Configuration du processeur.
        """
        self.config: Dict[str, str] = config
        self.cache: Optional[List[str]] = None
    
    def process(self, data: List[str]) -> List[str]:
        """Traite les données.
        
        Args:
            data: Liste des données à traiter.
            
        Returns:
            Liste des données traitées.
        """
        return [item.upper() for item in data]
```

---

## Versioning sémantique

### Format de version

Le projet doit suivre le **Semantic Versioning** (SemVer) : `MAJOR.MINOR.PATCH`

- **MAJOR** : Changements incompatibles avec les versions précédentes
- **MINOR** : Nouvelles fonctionnalités rétrocompatibles
- **PATCH** : Corrections de bugs rétrocompatibles

### Gestion des versions

- La version du projet doit être définie dans `pyproject.toml` dans `[project.version]`
- Chaque release doit être taguée dans Git avec le format `vMAJOR.MINOR.PATCH`
- Les versions de développement peuvent utiliser des suffixes : `0.1.0-dev`, `1.2.3-alpha`, etc.

### Changelog

- Un fichier `CHANGELOG.md` doit être maintenu à la racine du projet
- Chaque version doit avoir une entrée dans le changelog avec :
  - Date de release
  - Liste des changements (Added, Changed, Deprecated, Removed, Fixed, Security)
- Le format recommandé suit le standard [Keep a Changelog](https://keepachangelog.com/)

### Exemple de changelog

```markdown
# Changelog

## [1.2.0] - 2024-01-15

### Added
- Nouvelle fonctionnalité de validation des données
- Support des fichiers JSON

### Changed
- Amélioration des performances du processeur

### Fixed
- Correction du bug de parsing des fichiers CSV

## [1.1.0] - 2024-01-01

### Added
- Support initial du projet
```

---

## Gestion des dépendances

### Séparation des dépendances

- **Dépendances de production** : Dans `[project.dependencies]`
  - Uniquement les packages nécessaires à l'exécution du projet
- **Dépendances de développement** : Dans `[project.optional-dependencies.dev]`
  - Outils de développement (pytest, black, pylint, mypy, etc.)
  - Outils de build et de packaging

### Contraintes de versions

- **Format recommandé** : `package>=version,<next_major`
  - Exemple : `pytest>=7.0.0,<8.0.0`
- **Justification** : Permet les mises à jour de patch et minor tout en évitant les breaking changes
- **Exceptions** : Documenter dans le journal de développement si une version exacte ou une plage différente est nécessaire

### Mise à jour des dépendances

- Documenter les raisons des mises à jour dans le journal de développement
- Tester après chaque mise à jour de dépendance
- Maintenir un fichier `requirements.txt` ou `requirements-dev.txt` si nécessaire pour la compatibilité avec d'anciens outils

---

## Standards de nommage

### Conventions PEP 8

Le projet doit respecter strictement les conventions de nommage PEP 8 :

- **Classes** : `PascalCase`
  - Exemple : `DataProcessor`, `FileHandler`, `ValidationException`
- **Fonctions et méthodes** : `snake_case`
  - Exemple : `process_data()`, `validate_input()`, `get_user_info()`
- **Constantes** : `UPPER_SNAKE_CASE`
  - Exemple : `MAX_RETRIES`, `DEFAULT_TIMEOUT`, `API_BASE_URL`
- **Variables** : `snake_case`
  - Exemple : `user_name`, `file_path`, `data_list`
- **Modules et packages** : `snake_case`
  - Exemple : `data_processor.py`, `file_handler.py`
- **Privé** : Préfixer avec un underscore `_` pour les membres privés
  - Exemple : `_internal_method()`, `_private_attribute`

### Règles supplémentaires

- **Noms explicites** : Les noms doivent être descriptifs et éviter les abréviations non évidentes
  - ❌ `proc_data()` → ✅ `process_data()`
  - ❌ `usr_nm` → ✅ `user_name`
- **Cohérence** : Respecter la même convention dans tout le projet
- **Éviter les noms réservés** : Ne pas utiliser les mots-clés Python comme noms de variables
- **Longueur raisonnable** : Équilibrer entre descriptivité et longueur (max 100 caractères par ligne)

---

## Git workflow

### Branches

- **Branche principale** : `main` ou `master` contient uniquement du code stable et testé
- **Branches de fonctionnalité** : `feature/nom-fonctionnalite`
  - Une branche par fonctionnalité ou correction
  - Nommage descriptif en `kebab-case`
- **Branches de correction** : `fix/nom-correction`
  - Pour les corrections de bugs
- **Branches de release** : `release/version` (optionnel)
  - Pour préparer une nouvelle version

### Messages de commit

Le projet doit suivre le standard **Conventional Commits** :

- **Format** : `<type>(<scope>): <description>`
- **Types** :
  - `feat` : Nouvelle fonctionnalité
  - `fix` : Correction de bug
  - `docs` : Documentation uniquement
  - `style` : Formatage, point-virgules manquants, etc. (pas de changement de code)
  - `refactor` : Refactoring du code
  - `test` : Ajout ou modification de tests
  - `chore` : Tâches de maintenance (dépendances, build, etc.)
- **Scope** : Optionnel, indique la partie du projet affectée
- **Description** : Courte description en français ou anglais, impératif présent

### Exemples de messages

```
feat(core): ajout de la classe DataProcessor
fix(parser): correction du parsing des fichiers CSV
docs(readme): mise à jour des instructions d'installation
test(utils): ajout de tests pour file_parser
refactor(exceptions): réorganisation de la hiérarchie d'exceptions
chore(deps): mise à jour de pytest vers 7.4.0
```

### Workflow de contribution

1. Créer une branche depuis `main`
2. Développer la fonctionnalité avec des commits réguliers
3. S'assurer que tous les tests passent et que la couverture est maintenue
4. Vérifier que le code passe tous les outils de qualité
5. Créer une Pull Request vers `main`
6. La PR doit être revue et approuvée avant merge

---

## Objectif

Ces contraintes ont pour but de mettre en place de **bonnes pratiques de développement** pour les projets et modules Python, garantissant :

- **Maintenabilité** : Code organisé et documenté
- **Qualité** : Standards élevés de qualité et de sécurité
- **Traçabilité** : Journal de développement pour suivre l'évolution
- **Fiabilité** : Tests unitaires avec couverture élevée
- **Cohérence** : Configuration centralisée et standards uniformes

---

## Respect des contraintes

Ces contraintes doivent être respectées pour **tous** les développements du projet. En cas de non-respect, le code ne pourra pas être intégré dans la branche principale.
