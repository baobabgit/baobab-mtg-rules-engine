# Cahier des charges — `baobab-mtg-rules-engine`

## 1. Présentation du projet

### 1.1 Nom

`baobab-mtg-rules-engine`

### 1.2 Finalité

`baobab-mtg-rules-engine` est la librairie responsable de la modélisation et de l'exécution des règles de jeu de **Magic: The Gathering**.

Elle doit fournir un moteur de règles déterministe, inspectable et testable, capable de :

- représenter un état de partie complet ;
- calculer les actions légales à un instant donné ;
- exécuter des transitions d'état conformes aux règles ;
- gérer la pile, la priorité, les zones, les blessures, les capacités et les effets dans le périmètre retenu ;
- permettre des simulations automatiques et du self-play ;
- servir de socle au deckbuilder, à la plateforme et à des agents externes.

Le moteur ne doit pas seulement « jouer une partie » : il doit constituer une **brique métier profonde** de l'écosystème Baobab, utilisable dans des contextes de simulation, de validation d'interactions, de benchmark et de non-régression.

## 2. Positionnement dans l'écosystème

### 2.1 Place dans l'architecture

La librairie est une brique centrale consommée notamment par :

- `baobab-mtg-deckbuilder` ;
- `baobab-mtg-platform` ;
- éventuellement `baobab-mtg-api`.

### 2.2 Dépendances autorisées

La librairie peut dépendre de :

- `baobab-mtg-catalog`.

Cette dépendance doit rester **métier et structurée**, idéalement derrière des interfaces ou adaptateurs afin de découpler :

- le moteur de règles ;
- la source des définitions de cartes ;
- les données d'extensions, types, capacités et métadonnées nécessaires.

### 2.3 Dépendances interdites

La librairie ne doit pas dépendre de :

- l'API HTTP ;
- le front-end ;
- la gestion de collection utilisateur ;
- les produits scellés ;
- les probabilités d'ouverture ;
- la logique d'optimisation de deck.

## 3. Objectifs produit

La librairie doit permettre les usages suivants :

- démarrer une partie à partir de deux decks donnés ;
- calculer les actions légales d'un joueur à un instant donné ;
- exécuter une action choisie par un humain, un bot ou un agent ;
- résoudre des sorts et capacités ;
- rejouer un scénario déterministe ;
- simuler une partie complète jusqu'à sa fin ;
- exposer un historique exploitable pour les tests, l'analyse et le debug.

## 4. Périmètre fonctionnel

## 4.1 Périmètre cible initial (obligatoire pour la première version exploitable)

La première version exploitable du moteur doit se concentrer sur un **périmètre strict, fiable et extensible**, couvrant :

- parties à **deux joueurs uniquement** ;
- règles de base du jeu ;
- état de partie complet ;
- gestion des zones principales : bibliothèque, main, champ de bataille, cimetière, exil, pile ;
- structure du tour : début, phase principale, combat, fin de tour ;
- priorité et passage de priorité ;
- jeu de terrains ;
- lancement de sorts simples ;
- résolution de la pile ;
- créatures simples ;
- rituels simples ;
- éphémères simples ;
- ciblage simple ;
- blessures simples ;
- destruction simple ;
- changements de zone simples ;
- capacités activées simples ;
- capacités déclenchées simples ;
- fin de partie sur total de points de vie à 0 ou moins ;
- défaite à la pioche si bibliothèque vide au moment de piocher ;
- validation de légalité avant exécution d'action.

## 4.2 Périmètre explicitement hors version initiale

Les éléments suivants doivent être **hors scope** de la première version, sauf si nécessaires comme points d'extension vides :

- multijoueur ;
- Commander ;
- Brawl ;
- Planechase ;
- Archenemy ;
- sous-parties ;
- couches complètes ;
- effets de remplacement avancés ;
- effets de prévention avancés ;
- copies complexes ;
- cartes double face complexes ;
- cartes assimilées, sagas, conspirations, plans ;
- contrôle d'un autre joueur ;
- monarque, initiative, énergie et autres désignations avancées ;
- tournois, raccourcis compétitifs, règles de tournoi ;
- intelligence artificielle de décision ;
- UX, CLI, API, persistance de partie.

## 4.3 Périmètre d'extension prévu

L'architecture doit prévoir l'ajout futur de :

- effets continus plus riches ;
- remplacements et préventions ;
- jetons ;
- marqueurs ;
- copies ;
- counters et modifications temporaires ;
- variantes de format ;
- règles multijoueurs ;
- moteur de scénarios ;
- replays complets ;
- observabilité avancée.

## 5. Référentiel métier et source normative

### 5.1 Source de vérité métier

Le développement doit s'appuyer sur :

- la définition fonctionnelle du projet `baobab-mtg-rules-engine` ;
- le document des règles complètes de Magic disponible dans le projet.

### 5.2 Règles à prendre en compte dans la conception initiale

La modélisation doit intégrer au minimum les familles de règles suivantes :

- objets et caractéristiques ;
- joueurs ;
- zones ;
- structure du tour ;
- actions spéciales ;
- timing et priorité ;
- coûts ;
- lancement des sorts ;
- capacités activées ;
- capacités déclenchées ;
- résolution des sorts et capacités ;
- blessures ;
- points de vie ;
- actions basées sur un état ;
- ciblage ;
- changements de zone.

### 5.3 Exigence d'implémentation progressive

Le moteur **ne doit pas chercher à implémenter l'intégralité de Magic dès la première itération**. Il doit :

- implémenter correctement un noyau réduit ;
- rendre explicite ce qui est supporté ;
- refuser proprement ce qui n'est pas encore supporté ;
- documenter les extensions futures.

## 6. Exigences fonctionnelles détaillées

### 6.1 Représentation de l'état de partie

Le moteur doit exposer un état de partie inspectable, sérialisable si utile, et structuré autour de concepts explicites.

L'état doit au minimum représenter :

- identifiant de partie ;
- joueurs ;
- joueur actif ;
- joueur prioritaire ;
- numéro de tour ;
- phase courante ;
- étape courante ;
- total de points de vie ;
- bibliothèque de chaque joueur ;
- main de chaque joueur ;
- champ de bataille ;
- cimetière ;
- exil ;
- pile ;
- nombre de terrains joués dans le tour ;
- historique minimal des événements ;
- état terminal éventuel ;
- vainqueur éventuel ;
- perdant(s) éventuel(s) ;
- informations nécessaires aux actions basées sur un état.

### 6.2 Représentation des objets de jeu

Le moteur doit distinguer clairement :

- carte de référence ;
- carte en partie ;
- permanent ;
- sort sur la pile ;
- capacité sur la pile ;
- source d'effet ;
- cible ;
- zone ;
- action demandée ;
- action résolue ;
- événement produit.

Chaque objet de jeu doit disposer d'un identifiant technique stable pendant sa durée de vie en zone. Un objet qui change de zone doit être traité comme un **nouvel objet métier**, sauf exceptions explicitement gérées par les règles supportées.

### 6.3 Démarrage de partie

Le moteur doit permettre :

- l'initialisation à partir de deux decks ;
- le mélange des bibliothèques ;
- la détermination du joueur qui commence ;
- la pioche des mains de départ ;
- la gestion d'un mulligan simplifié ou complet selon la stratégie retenue ;
- l'entrée dans le premier tour.

Le choix retenu pour le mulligan doit être documenté et testé.

### 6.4 Structure du tour

Le moteur doit gérer au minimum :

- phase de début ;
- étape de dégagement ;
- étape d'entretien ;
- étape de pioche ;
- phase principale pré-combat ;
- phase de combat ;
- phase principale post-combat ;
- étape de fin ;
- étape de nettoyage.

Le moteur doit également gérer :

- le passage automatique entre étapes quand la pile est vide et que tous les joueurs passent ;
- la suppression du mana résiduel quand requis dans le périmètre retenu ;
- les vérifications d'actions basées sur un état avant attribution de la priorité.

### 6.5 Priorité et pile

Le moteur doit permettre :

- de savoir quel joueur a la priorité ;
- de calculer les actions légales à ce moment ;
- de passer la priorité ;
- de mettre un sort ou une capacité sur la pile ;
- de résoudre l'objet au sommet de la pile lorsque tous passent successivement ;
- d'attribuer de nouveau la priorité au bon joueur après résolution.

La pile doit être modélisée explicitement et séparée des événements produits.

### 6.6 Actions légales

Le moteur doit pouvoir calculer, à partir d'un état donné, une liste d'actions légales comprenant au minimum :

- passer la priorité ;
- jouer un terrain si permis ;
- lancer un sort depuis la main si autorisé ;
- activer une capacité simple si autorisée ;
- déclarer des attaquants dans le périmètre retenu ;
- déclarer des bloqueurs si le périmètre retenu le gère ;
- effectuer des choix demandés lors d'une résolution.

Les actions doivent être :

- déterministes ;
- validables ;
- sérialisables si possible ;
- lisibles par un agent externe.

### 6.7 Lancement de sorts

Le moteur doit gérer un cycle complet de lancement pour le périmètre retenu :

- vérification du timing ;
- vérification des restrictions ;
- sélection éventuelle des cibles ;
- calcul du coût ;
- paiement du coût ;
- mise sur la pile ;
- historique de l'action.

### 6.8 Capacités

Le moteur doit gérer une modélisation distincte des :

- capacités statiques simples si indispensables au périmètre ;
- capacités activées simples ;
- capacités déclenchées simples ;
- effets de résolution associés.

Les capacités déclenchées doivent au minimum :

- se déclencher au bon moment ;
- être mises sur la pile au bon moment ;
- être contrôlées par le bon joueur ;
- produire leur effet à la résolution.

### 6.9 Ciblage

Le moteur doit fournir un système de ciblage permettant :

- de décrire une contrainte de cible ;
- d'énumérer les cibles légales ;
- de valider une cible choisie ;
- de vérifier la légalité à la résolution ;
- d'annuler ou contrecarrer implicitement un effet si toutes ses cibles deviennent illégales, selon le périmètre supporté.

### 6.10 Combat et blessures

Le moteur doit couvrir un combat simple comprenant :

- ouverture de la phase de combat ;
- déclaration des attaquants ;
- déclaration des bloqueurs si supportée ;
- assignation simple des blessures de combat ;
- application des blessures ;
- destruction par blessures létales via actions basées sur un état.

### 6.11 Changements de zone

Le moteur doit gérer correctement les changements suivants :

- bibliothèque vers main ;
- main vers pile ;
- pile vers champ de bataille ;
- pile vers cimetière ;
- champ de bataille vers cimetière ;
- toute transition simple vers exil si une carte supportée le demande.

Les changements de zone doivent produire des événements explicites et mettre à jour les identités runtime correctement.

### 6.12 Conditions de fin de partie

Le moteur doit détecter au minimum :

- joueur à 0 point de vie ou moins ;
- tentative de pioche dans une bibliothèque vide ;
- concession si le cas d'usage est supporté ;
- victoire d'un joueur quand l'autre perd.

## 7. Exigences de conception logicielle

### 7.1 Principes d'architecture

L'architecture doit respecter les principes suivants :

- moteur déterministe ;
- transitions d'état explicites ;
- séparation claire entre données, règles, validation et exécution ;
- séparation entre stratégie de décision et moteur de règles ;
- extensibilité par règles, effets et handlers ;
- forte testabilité unitaire ;
- minimisation des effets de bord ;
- refus explicite des cas non supportés.

### 7.2 Style d'architecture recommandé

Une architecture orientée domaine est attendue, avec séparation explicite entre :

- modèles métier ;
- règles et validateurs ;
- services d'application / orchestrateurs ;
- événements de jeu ;
- effets ;
- capacités ;
- actions ;
- exceptions métier.

### 7.3 Concepts attendus

La librairie doit proposer des concepts proches de :

- `Game` ;
- `GameState` ;
- `PlayerState` ;
- `Zone` ;
- `StackObject` ;
- `Action` ;
- `Ability` ;
- `Effect` ;
- `Trigger` ;
- `GameEvent` ;
- `RulesEngine` ;
- `ActionResolver` ;
- `StateBasedActionChecker` ;
- `PriorityManager` ;
- `TurnManager`.

Les noms exacts peuvent varier, mais la responsabilité doit rester claire.

### 7.4 Politique de support des cartes

Le moteur ne doit pas coder les cartes « en dur » partout dans le noyau.

Il faut viser :

- un noyau de règles génériques ;
- des définitions de cartes exploitables ;
- une couche d'adaptation entre caractéristiques de carte et comportements runtime ;
- des implémentations spécifiques limitées aux comportements réellement supportés.

### 7.5 Politique de non-support

Quand une carte, capacité ou interaction n'est pas supportée, la librairie doit :

- le signaler explicitement ;
- lever une exception projet spécifique adaptée ;
- documenter la limite ;
- ne jamais produire silencieusement un résultat faux.

## 8. Exigences de développement et de qualité

Le développement doit respecter strictement les contraintes du projet.

### 8.1 Structure du projet

Le projet doit respecter une structure de type :

```text
src/baobab_mtg_rules_engine/
tests/
docs/
```

### 8.2 Organisation orientée classe

- une classe par fichier ;
- noms de fichiers en `snake_case` ;
- noms de classes en `PascalCase` ;
- organisation par sous-domaines cohérents.

### 8.3 Exceptions personnalisées

Toutes les erreurs spécifiques au projet doivent hériter d'une exception racine dédiée, par exemple :

- `BaobabMtgRulesEngineException`.

Des exceptions dédiées sont attendues, par exemple :

- `UnsupportedRuleException` ;
- `IllegalActionException` ;
- `InvalidTargetException` ;
- `InvalidGameStateException` ;
- `UnsupportedCardBehaviorException` ;
- `CatalogIntegrationException`.

### 8.4 Type hints

Toutes les fonctions, méthodes, attributs et retours doivent être typés.

### 8.5 Outils obligatoires

Le code doit passer sans erreur :

- `black` ;
- `pylint` ;
- `mypy` ;
- `flake8` ;
- `bandit`.

### 8.6 Configuration centralisée

La configuration doit être centralisée dans `pyproject.toml` autant que possible.

### 8.7 Tests unitaires

Les tests doivent respecter :

- un fichier de test par classe ;
- arborescence miroir du code ;
- classes de test dédiées ;
- couverture minimale de 90 %.

### 8.8 Documentation obligatoire

Le projet doit contenir :

- `README.md` ;
- `CHANGELOG.md` ;
- `docs/dev_diary.md` ;
- documentation des limites de périmètre ;
- exemples d'utilisation.

### 8.9 Git workflow

Le développement doit suivre :

- une branche dédiée par feature ;
- des commits de type Conventional Commits ;
- une pull request par feature ;
- merge sur `main` uniquement si tests, qualité et contraintes sont validés.

## 9. Exigences de test

## 9.1 Principes

Le moteur doit être conçu **par le test** sur ses invariants métier.

Il faut couvrir au minimum :

- création d'état initial ;
- pioche ;
- jeu de terrain ;
- lancement de sort ;
- validation de légalité ;
- priorité ;
- résolution de pile ;
- capacités déclenchées simples ;
- blessures ;
- destruction ;
- changement de zone ;
- fin de partie ;
- refus des cas non supportés.

## 9.2 Niveaux de tests attendus

Les tests doivent inclure :

- tests unitaires par classe ;
- tests de services métier ;
- tests de scénarios de partie ;
- tests de non-régression sur interactions supportées ;
- tests de déterminisme à seed donnée si l'aléatoire est injecté.

## 9.3 Cas de tests minimaux attendus

Des scénarios minimaux doivent exister pour :

1. démarrage de partie ;
2. pioche initiale ;
3. jeu d'un terrain pendant la phase principale ;
4. interdiction de jouer un second terrain si non autorisé ;
5. lancement d'un rituel pendant la phase principale avec pile vide ;
6. refus d'un rituel en dehors du timing légal ;
7. lancement d'un éphémère en réponse ;
8. passage de priorité et résolution du sommet de pile ;
9. capacité déclenchée simple mise sur la pile ;
10. créature détruite par blessures létales après vérification SBA ;
11. défaite par points de vie ;
12. défaite par pioche impossible ;
13. changement de zone créant un nouvel objet runtime ;
14. refus explicite d'une carte ou règle non supportée.

## 10. Livrables attendus

L'IA de développement doit produire au minimum :

- le code source complet ;
- la structure de projet Python packagée ;
- `pyproject.toml` correctement configuré ;
- les tests unitaires ;
- la configuration de couverture ;
- `README.md` ;
- `CHANGELOG.md` ;
- `docs/dev_diary.md` ;
- une documentation de périmètre supporté ;
- des exemples de scénarios ;
- les exceptions métier dédiées.

## 11. Proposition d'arborescence cible

```text
src/baobab_mtg_rules_engine/
├── __init__.py
├── constants/
├── enums/
├── exceptions/
├── interfaces/
├── models/
│   ├── cards/
│   ├── game/
│   ├── actions/
│   ├── abilities/
│   ├── effects/
│   ├── events/
│   └── zones/
├── services/
│   ├── bootstrap/
│   ├── game_flow/
│   ├── priority/
│   ├── actions/
│   ├── stack/
│   ├── combat/
│   ├── resolution/
│   ├── state_based_actions/
│   └── catalog/
├── factories/
├── validators/
├── policies/
└── utils/

tests/
├── baobab_mtg_rules_engine/
│   ├── exceptions/
│   ├── models/
│   ├── services/
│   ├── validators/
│   └── factories/
└── scenarios/

docs/
├── dev_diary.md
├── architecture.md
├── supported_scope.md
└── tests/
    └── coverage/
```

## 12. Stratégie d'implémentation recommandée

Le développement doit se faire de manière incrémentale.

### Lot 1 — socle projet

- bootstrap du package ;
- configuration qualité ;
- hiérarchie d'exceptions ;
- modèles de base ;
- tests de structure.

### Lot 2 — état de jeu minimal

- `GameState` ;
- `PlayerState` ;
- zones ;
- objets runtime ;
- bootstrap de partie.

### Lot 3 — boucle de tour minimale

- tours ;
- phases ;
- étapes ;
- pioche ;
- priorité ;
- passage d'étape.

### Lot 4 — actions de base

- jeu de terrain ;
- sorts simples ;
- calcul des actions légales ;
- pile.

### Lot 5 — résolution et effets simples

- résolution des sorts ;
- changements de zone ;
- effets simples ;
- ciblage simple.

### Lot 6 — combat et blessures

- déclaration d'attaquants ;
- bloqueurs simples ;
- blessures ;
- destruction.

### Lot 7 — capacités

- capacités activées simples ;
- capacités déclenchées simples ;
- mise sur pile ;
- résolution.

### Lot 8 — fiabilisation

- scénarios complets ;
- refus des cas non supportés ;
- documentation de périmètre ;
- couverture et qualité.

## 13. Critères d'acceptation

Le projet sera considéré conforme si :

1. la librairie est installable et importable ;
2. l'architecture respecte les contraintes de développement ;
3. le moteur supporte correctement le périmètre initial annoncé ;
4. les cas non supportés sont refusés explicitement ;
5. la pile, la priorité, les zones et les transitions principales sont testées ;
6. les scénarios simples de partie sont rejouables ;
7. les tests atteignent au moins 90 % de couverture ;
8. `black`, `pylint`, `mypy`, `flake8` et `bandit` passent ;
9. la documentation explique clairement ce qui est supporté et ce qui ne l'est pas ;
10. le moteur est exploitable par une IA ou un agent externe via des objets d'action lisibles.

## 14. Consignes explicites pour l'IA de développement

L'IA de développement doit impérativement :

- respecter ce cahier des charges ;
- respecter les contraintes de développement du projet ;
- développer en plusieurs incréments sûrs ;
- ne pas implémenter de fausses règles pour « faire passer » les tests ;
- privilégier un moteur exact sur petit périmètre plutôt qu'un moteur large mais incorrect ;
- documenter toute hypothèse de simplification ;
- documenter tout cas non supporté ;
- créer une branche dédiée pour chaque feature ;
- exécuter les tests et contrôles qualité avant PR ;
- merger sur `main` uniquement après validation complète.

## 15. Résultat attendu

À l'issue du développement, `baobab-mtg-rules-engine` doit fournir un **noyau de moteur de règles fiable, déterministe, testable et extensible**, capable d'exécuter un sous-ensemble cohérent de parties de Magic: The Gathering et de servir de socle solide pour les briques supérieures de l'écosystème Baobab.
