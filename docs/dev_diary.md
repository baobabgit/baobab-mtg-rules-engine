# Journal de développement — baobab-mtg-rules-engine

Les entrées les plus récentes en premier.

## 2026-04-09 — feature `09_triggered_abilities_core`

### Modifications

- `domain/` : ajout de `TriggeredAbilityDefinition`, `PendingTriggeredAbility`, `TriggeredAbilityStackObject`
- `GameState` : file de triggers en attente, vues de capacités déclenchées sur la pile, séquence de scan d’événements, compteurs de passes non pile-vide
- `EventType` : événements `TRIGGER_DETECTED`, `TRIGGER_QUEUED`, `TRIGGER_STACKED`, `TRIGGER_RESOLVED`, `TRIGGER_FIZZLED`
- `catalog/` : extension de `CardGameplayPort` avec `triggered_ability_definitions` ; support mémoire via `InMemoryCardCatalogAdapter` ; refus explicite côté `BaobabMtgCatalogAdapter`
- `engine/trigger_detection_service.py` : détection déclenchée sur journal (ETB, dies, cast, begin step, draw, combat damage to player)
- `stack/triggered_ability_resolution_service.py` : résolution/fizzle des capacités déclenchées simples (damage opponent/player, destroy target creature, draw cards)
- `TurnManager` : intégration du pipeline complet détecté → file → empilé au bon moment (après SBA, avant ré-attribution de priorité), APNAP duel déterministe, résolution de pile unifiée sort/capacité
- `PriorityManager` : mode duel supportant fermeture de fenêtre à pile non vide (résolution par deux passes)
- tests : nouvelles suites `test_triggered_ability_flow.py`, `test_trigger_detection_service.py`, `test_triggered_ability_resolution_service.py` + extensions catalog/priority/event types
- documentation : README enrichi (section « Capacités déclenchées (feature 09) »)

### Buts

- Fournir un noyau réel de capacités déclenchées simples, déterministe et traçable
- Respecter l’ordre d’empilement APNAP en duel et le timing moteur (pas d’empilement pendant résolution d’un autre objet)

### Impact

- Les consommateurs peuvent désormais injecter des capacités déclenchées via le catalogue mémoire
- Le journal moteur expose explicitement le cycle trigger (détection, queue, stack, résolution/fizzle)

## 2026-04-06 — CI sur tags + release GitHub (v1.0.0)

### Modifications

- `.github/workflows/ci.yml` : trigger **tags** `v*.*.*` uniquement ; job vérifiant que le commit est sur `main` ; `quality` inchangé ; job `release` avec `softprops/action-gh-release` et wheel/sdist
- Version package **1.0.0** ; `CHANGELOG` ; README et `docs/release_readiness.md` alignés

## 2026-04-06 — release readiness (publication)

### Modifications

- `LICENSE` propriétaire (all rights reserved) ; `MANIFEST.in` ; `pyproject.toml` : `license = { file = "LICENSE" }`, URLs `baobabgit/baobab-mtg-rules-engine`, classifiers Alpha + Proprietary, version **0.8.1**
- `.github/workflows/ci.yml` : CI push/PR `main` (black, flake8, mypy, pylint, bandit, pytest+couverture, build + artefacts)
- README : statut projet, publication/build, licence ; `docs/release_readiness.md` ; `CHANGELOG` **0.8.1**

### Buts

- Dépôt publiable et vérifiable automatiquement sans ambiguïté de licence ni d’URL

### Note PR / merge

- Branche `feature/release-readiness-go` → PR [#9](https://github.com/baobabgit/baobab-mtg-rules-engine/pull/9) squash-merge sur `main`

## 2026-04-05 — feature `08_scenarios_replay_and_observability`

### Modifications

- `scenarios/` : `ScenarioBuilder`, `ScenarioContext` (construction déterministe, alias stables pour replay)
- `replay/` : `RecordedGameAction`, `GameReplayService` (replay, assertions déterminisme / trace)
- `observability/` : `GameStateInspector` (trace tuple, formatage événements, résumé)
- `ReplaySequenceError` ; tests miroir replay / scénarios / observabilité + fixtures de non-régression
- README (section scénarios & replay), `docs/features/08_scenarios_replay_and_observability.md`, `examples/replay_minimal_example.py`, version **0.8.0** ; couverture **~92 %**

### Buts

- Tests de non-régression reproductibles, debug et inspection du journal sans persistance externe ni UI

### Impact

- Les alias doivent être cohérents avec le `ScenarioBuilder` pour que le replay résolve les bons `GameObjectId`

### Note PR / merge

- Branche `feature/08-scenarios-replay-and-observability` → PR [#8](https://github.com/baobabgit/baobab-mtg-rules-engine/pull/8) squash-merge sur `main` (commit `296b039`)

## 2026-04-06 — feature `06_combat_damage_and_sba`

### Modifications

- `combat/` : `CombatService`, `AttackerDeclarationService`, `BlockerDeclarationService` ; `engine/state_based_action_service.py`
- `Permanent` : blessures marquées ; `GameState` : issue de partie, défaite / match nul, garde sur déclarations si partie terminée, un bloqueur par attaquant en domaine
- `CardGameplayPort` / `InMemoryCardCatalogAdapter` : `creature_power` / `creature_toughness` ; `BaobabMtgCatalogAdapter` : refus explicite
- `LegalActionService` : P/T > 0 pour proposer attaquant / bloqueur, pas de second bloqueur sur le même attaquant ; application via services de déclaration
- `TurnManager` : `rules` optionnel (combat + ABS à `COMBAT_DAMAGE`), pioche impossible → défaite, nettoyage des blessures marquées
- Événements combat / ABS / victoire ; tests miroir `tests/.../combat/`, `test_state_based_action_service.py` ; README, CHANGELOG, version **0.7.0** ; couverture **~91 %**

### Buts

- Combat déterministe, destruction létale, fin de partie par PV ou bibliothèque vide

### Impact

- Les consommateurs doivent fournir P/T catalogue pour les créatures en combat ; le moteur refuse le multi-blocage simple

### Note PR / merge

- Branche `feature/06-combat-damage-and-sba` → PR [#7](https://github.com/baobabgit/baobab-mtg-rules-engine/pull/7) squash-merge sur `main`

## 2026-04-06 — feature `05_casting_stack_and_resolution`

### Modifications

- `StackObject`, `SpellCastService`, `StackResolutionService`, `TargetValidator`, `SimpleTarget` ; `InvalidSpellTargetError` ; vues pile sur `GameState` ; événements `SPELL_RESOLVED`, `SPELL_FIZZLED`, `PLAYER_DAMAGED`
- `LegalActionService` : sorts avec cibles déterministes, application via lancement réel ; refactor `_cast_spell_actions_for_hand_card` (pylint `too-many-locals`)
- `CardGameplayPort` / adaptateurs mémoire et Baobab pour créatures-sort, cibles et dégâts joueur (hors périmètre = `UnsupportedRuleException` côté Baobab)
- Tests miroir + `cast_spell_test_helpers.py` ; `pyproject.toml` : `min-similarity-lines` pylint pour le bruit des tests ; `simple_target` sans `assert` (bandit B101)
- README (section pile / résolution), CHANGELOG, version **0.6.0** ; couverture **~94 %**

### Buts

- Chaîne lancer → empiler → résoudre avec revalidation des cibles et fizzle explicite

### Impact

- Base pour des effets plus riches sans perdre le déterminisme ni l’inspectabilité

### Note PR / merge

- Branche `feature/05-casting-stack-and-resolution` → PR [#6](https://github.com/baobabgit/baobab-mtg-rules-engine/pull/6) squash-merge sur `main` après contrôles qualité au vert

## 2026-04-05 — feature `04_legal_actions_engine`

### Modifications

- Paquet `actions` : `SupportedActionKind`, `GameAction` et actions concrètes (passe, terrain, sort, capacité simple, attaquants / bloqueurs)
- `CardGameplayPort`, `InMemoryCardCatalogAdapter` enrichi (terrains, créatures, rituels / instants, coûts, capacités activées) ; `BaobabMtgCatalogAdapter` refuse le gameplay distant avec tests dédiés
- `LegalActionService` : `compute_legal_actions`, `apply_action` (re-validation dans l’ensemble légal courant avant toute mutation)
- `IllegalGameActionError` ; `TurnManager` : reset compteur de terrains au roulement de tour, vidage des déclarations de combat à l’entrée en `BEGIN_COMBAT`
- `GameState` : compteur de terrains / combat et `apply_*` alignés avec la feature (déjà présents sur la branche)
- Tests miroir `tests/.../actions/`, `test_legal_action_service.py`, extension `test_turn_manager` / catalogue ; README, CHANGELOG, version **0.5.0** ; couverture **~95 %**

### Buts

- Offrir une liste d’actions **déterministe** et **inspectable** pour l’agent ou l’UI, sans logique de choix ni exécution de règles non supportées

### Impact

- Base pour des résolveurs de pile et un combat plus fin sans coupler le moteur à une stratégie joueur

### Note PR / merge

- Branche `feature/04-legal-actions-engine` → PR vers `main` ; merge après CI locale au vert

## 2026-04-05 — feature `03_turn_loop_priority`

### Modifications

- Paquet `engine` : `TurnManager` (orchestration), `PriorityManager` (pile vide / non vide), `StepTransitionService` (ordre `STANDARD_DUEL_STEP_ORDER`), port de légalité avant `pass_priority`
- `GameState` : champs priorité + `establish_duel_opening_player` ; `PlayerState` : mana flottant entier vidé au nettoyage
- `domain.step` : `COMBAT_STEPS`, `STANDARD_DUEL_STEP_ORDER` (évite la duplication avec le moteur)
- Nouveaux `EventType` pour étapes, priorité, pioche et mana
- Tests miroir `tests/baobab_mtg_rules_engine/engine/` ; README ; CHANGELOG / version **0.4.0** ; couverture **100 %**

### Buts

- Faire avancer un duel de façon déterministe et traçable sans logique « joueur » dans le moteur (passes injectées)

### Impact

- Base pour la pile, les sorts et le combat détaillé dans les prochaines features

### Note PR / merge

- Branche `feature/03-turn-loop-priority` → PR vers `main` ; merge après revue et CI locale au vert.

## 2026-04-05 — feature `02_game_setup_and_zones`

### Modifications

- Setup 1v1 déterministe : `GameFactory`, `GameSetupRequest`, validation `DeckValidator`, construction bibliothèque, mélange (`GameState.shuffle_player_library`), pioche initiale et mulligan (`MulliganPolicy`, port `MulliganChoicePort`)
- Catalogue : `CardDefinitionPort`, `InMemoryCardCatalogAdapter`, `BaobabMtgCatalogAdapter` (refus explicite si paquet ou API absents)
- `EventType` enrichi (`SETUP_*`), `GameState.draw_cards_from_library_to_hand` avec validation avant mutation, `InsufficientLibraryError` / `DeckValidationError`
- Tests : setup nominal, graine, mulligan, pioche insuffisante sans défaite ni mutation partielle ; adaptateur catalogue mocké
- README (exemple setup), CHANGELOG / version **0.3.0** ; couverture **100 %** sur le package

### Buts

- Démarrer une partie inspectable à deux decks valides, tracer le setup, garder le moteur découplé des décisions de mulligan (injection)

### Impact

- Base pour la boucle de tour et les règles in-game sans élargir Commander / sideboard complet

### Note PR / merge

- Branche `feature/02-game-setup-and-zones` : ouvrir PR vers `main` après revue ; merge lorsque la CI locale est au vert.

## 2026-04-05 — feature `01_core_domain_model`

### Modifications

- Ajout du paquet `domain` : `Game`, `GameState`, `PlayerState`, `Zone`, `ZoneLocation`, `TurnState`, enums `ZoneType`, `Phase`, `Step`, objets `GameObject` / `InGameCard` / `Permanent` / `SpellOnStack` / `AbilityOnStack`, `GameObjectId`, `CardReference`, `GameEvent`, protocoles `AbilityLike` / `EffectLike`
- Exception `InvalidGameStateError` exportée au niveau racine
- Tests miroir, README / CHANGELOG / version **0.2.0**
- Contrôles : black, flake8, mypy, pylint (10/10), bandit, pytest — couverture **100 %** sur le package

### Buts

- Représenter une partie à deux joueurs inspectable, avec historique d’événements minimal et identifiants d’objets déterministes

### Impact

- Base pour les features boucle de tour, pile et règles sans introduire d’exécution de règles dans cette livraison

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
