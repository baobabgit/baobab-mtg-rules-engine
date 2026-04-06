# Feature 08 — Scénarios, replay, observabilité

## Objectif

Permettre des **tests de non-régression** reproductibles, le **debug** et la **simulation** en rejouant une séquence d’actions décrite de façon stable (alias logiques, pas d’identifiants d’objets figés entre deux constructions).

## Composants

| Module | Rôle |
|--------|------|
| `scenarios.scenario_builder` | Construction déterministe d’un `ScenarioContext` (état, alias, `TurnManager`, `LegalActionService`). |
| `replay.recorded_game_action` | `RecordedGameAction` : sérialisation d’actions supportées + résolution via `object_aliases`. |
| `replay.game_replay_service` | Application pas à pas ou replay complet ; assertions de déterminisme et de trace d’événements. |
| `observability.game_state_inspector` | Trace d’événements tuple (stable), formatage texte, résumé d’état. |

## Périmètre supporté

- Enregistrement et replay des familles d’actions alignées sur `SupportedActionKind` : passe, terrain, sort (0 ou 1 cible simple joueur / permanent), capacité activée simple, déclaration attaquant / bloqueur.
- Cibles de sort enregistrées : **aucune**, **joueur 0 ou 1**, **un permanent** référencé par alias.
- Scénarios de test : cartes en main, permanents au champ, mana flottant, tour / priorité, premier joueur du duel.
- Comparaison de traces via `GameStateInspector.event_trace_tuple` (ordre et charges utiles du journal moteur).

## Hors périmètre (refus explicite)

- **Persistance externe** (fichiers, base de données) : non fournie ; vous sérialisez vous-même les `RecordedGameAction` si besoin.
- **Interface graphique ou HTTP** : hors bibliothèque.
- Actions non modélisées par `GameAction` / enregistrement : `ReplaySequenceError` ou erreur métier existante à l’application.
- Sorts à **plusieurs cibles**, cibles non couvertes par `SimpleTarget`, ou enregistrement sans table `id_to_alias` complète : `ReplaySequenceError`.

## Déterminisme

Les `GameObjectId` sont émis dans l’ordre de construction du `GameState`. Pour comparer deux exécutions, utilisez le **même** enchaînement `ScenarioBuilder` et les **mêmes** alias ; le replay résout les alias vers les identifiants de cette construction.

## Références

- Exemple exécutable : `examples/replay_minimal_example.py`
- Tests : `tests/baobab_mtg_rules_engine/replay/`, `scenarios/`, `observability/`, `test_regression_fixtures.py`
