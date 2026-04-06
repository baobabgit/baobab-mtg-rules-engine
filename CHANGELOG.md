# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format s’inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [0.7.0] - 2026-04-06

### Added

- Paquet `combat` : `CombatService` (blessures à `COMBAT_DAMAGE`, un bloqueur par attaquant max), `AttackerDeclarationService`, `BlockerDeclarationService`
- `StateBasedActionService` : destruction des créatures avec blessures létales, défaite par PV, match nul si les deux joueurs sont à 0 ou moins
- `Permanent.marked_damage` ; `CardGameplayPort.creature_power` / `creature_toughness` et `creature_power_toughness_by_key` sur `InMemoryCardCatalogAdapter`
- `GameState` : fin de partie (`winner_player_index`, `is_draw_game`, `is_game_finished`), `record_player_defeat`, `record_draw_game`, vidage des blessures au nettoyage
- `TurnManager` : paramètre optionnel `rules` pour résoudre combat + ABS à `COMBAT_DAMAGE` ; pioche impossible à l’étape de pioche → défaite (`reason=library`)
- Événements `COMBAT_DAMAGE_ASSIGNED`, `CREATURE_DESTROYED`, `PLAYER_DEFEATED`, `GAME_VICTORY_ASSIGNED`, `GAME_DRAW`, `ALL_PERMANENT_DAMAGE_CLEARED`

### Tests

- `tests/.../combat/`, `engine/test_state_based_action_service.py`, extension `test_turn_manager` / `test_legal_action_service`

## [0.6.0] - 2026-04-06

### Added

- `StackObject` : vue métier d’un sort sur la pile (contrôleur, clé catalogue, cibles) ; `GameState` conserve des vues par identifiant d’objet pile
- `SpellCastService` : validation timing (rituel / créature / éphémère), coût mana générique, cibles via `TargetValidator`, migration main → pile avec `SpellOnStack`
- `StackResolutionService` : résolution LIFO du sommet, fizzle si toutes les cibles deviennent illégales, effets simples (créature → champ de bataille, dégâts joueur, défausse)
- `TargetValidator` et `SimpleTarget` : ciblage joueur / créature au lancement et revalidation à la résolution ; `InvalidSpellTargetError`
- `LegalActionService` : énumération des `CastSpellAction` avec cibles, application via `SpellCastService` ; événements `SPELL_RESOLVED`, `SPELL_FIZZLED`, `PLAYER_DAMAGED`
- Extension de `CardGameplayPort` / `InMemoryCardCatalogAdapter` (sort créature, type de cible, dégâts joueur) ; `BaobabMtgCatalogAdapter` refuse ces extensions jusqu’à branchement catalogue

### Tests

- `tests/.../casting/`, `stack/`, `targeting/` ; helpers partagés `cast_spell_test_helpers.py`

## [0.5.0] - 2026-04-05

### Added

- Paquet `actions` : modèle d’actions supportées (`SupportedActionKind`, sous-classes `GameAction`) : passe, terrain, sort, capacité activée simple, attaquants / bloqueurs
- `CardGameplayPort` et extension de `InMemoryCardCatalogAdapter` pour types, coûts génériques et capacités simples
- `LegalActionService` : liste déterministe d’actions légales et `apply_action` après re-validation d’appartenance à l’ensemble courant
- `IllegalGameActionError` ; `TurnManager` réinitialise les compteurs de tour au passage de joueur et vide les déclarations de combat à l’entrée en `BEGIN_COMBAT`

### Tests

- `tests/baobab_mtg_rules_engine/engine/test_legal_action_service.py`, miroir `tests/baobab_mtg_rules_engine/actions/`, couverture `BaobabMtgCatalogAdapter` (gameplay)

## [0.4.0] - 2026-04-05

### Added

- Paquet `baobab_mtg_rules_engine.engine` : `TurnManager`, `PriorityManager`, `StepTransitionService`, port `PriorityActionLegalityPort` et `NullPriorityActionLegalityPort`
- Boucle de tour duel : enchaînement UNTAP → … → CLEANUP, priorité à pile vide (deux passes), saut de pioche du premier tour du duel, vidage du mana flottant au nettoyage
- `GameState` : priorité inspectable, compteur de passes à pile vide, `establish_duel_opening_player` ; `PlayerState.floating_mana` ; constantes `COMBAT_STEPS` et `STANDARD_DUEL_STEP_ORDER` sur `domain.step`
- `EventType` : `TURN_STEP_ENTERED`, `TURN_STEP_ADVANCED`, `TURN_ROLLED_TO_NEXT_PLAYER`, `PRIORITY_*`, `TURN_DRAW_*`, `FLOATING_MANA_CLEARED`

### Tests

- `tests/baobab_mtg_rules_engine/engine/` : progression de tour, priorité, pile non vide, légalité avant passe

## [0.3.0] - 2026-04-05

### Added

- Sous-paquets `baobab_mtg_rules_engine.setup` et `baobab_mtg_rules_engine.catalog` : création de partie à deux joueurs (`GameFactory`, `GameSetupRequest`, `DeckDefinition`, `DeckValidator`), politique de mulligan parisien simplifié (`MulliganPolicy`, `MulliganChoicePort`, `CallbackMulliganChoice`), port catalogue (`CardDefinitionPort`) et adaptateurs `InMemoryCardCatalogAdapter`, `BaobabMtgCatalogAdapter`
- Événements de setup dans `EventType` (`SETUP_*`) ; pioche et mélange de bibliothèque déterministes sur `GameState` ; `Zone.replace_ordered_contents` pour les mélanges
- Exceptions `DeckValidationError`, `InsufficientLibraryError` (pioche impossible sans règle de défaite implicite)

### Tests

- Couverture miroir sous `tests/baobab_mtg_rules_engine/setup/`, `tests/baobab_mtg_rules_engine/catalog/`, extensions `domain` (pioche, zone)

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
