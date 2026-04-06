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

## Setup de partie (deux joueurs)

Le sous-paquet `baobab_mtg_rules_engine.setup` construit une `Game` à partir de decks décrits par des clés catalogue, avec mélange et mulligan **déterministes** lorsqu'une graine est fournie. Les décisions de mulligan sont injectées via `MulliganChoicePort` (le moteur n'embarque pas d'heuristique joueur).

```python
from baobab_mtg_rules_engine.catalog import InMemoryCardCatalogAdapter
from baobab_mtg_rules_engine.setup import (
    CallbackMulliganChoice,
    DeckDefinition,
    GameFactory,
    GameSetupRequest,
)

keys = frozenset(f"c{i}" for i in range(15)) | frozenset(f"d{i}" for i in range(15))
catalog = InMemoryCardCatalogAdapter(keys)
factory = GameFactory(catalog)
entries = tuple((f"c{i}", 4) for i in range(15))
deck0 = DeckDefinition("Alice", entries)
deck1 = DeckDefinition("Bob", tuple((f"d{i}", 4) for i in range(15)))
request = GameSetupRequest(
    game_id="demo",
    player_names=("Alice", "Bob"),
    decks=(deck0, deck1),
    rng_seed=123,
    starting_player=0,
)
game = factory.create_game(request, CallbackMulliganChoice(lambda _p, _d, _h: False))
```

Pour brancher le catalogue distribué Baobab, utiliser `BaobabMtgCatalogAdapter` si le paquet `baobab-mtg-catalog` est installé et expose l'API attendue ; sinon une `UnsupportedRuleException` est levée.

## Boucle de tour et priorité (duel)

Le paquet `baobab_mtg_rules_engine.engine` fournit `TurnManager` pour enchaîner les étapes (dégagement → entretien → pioche → principales → combat simplifié → fin → nettoyage), gérer la **priorité** et avancer lorsque la **pile est vide** et que **chaque joueur a passé** successivement. Le premier tour du joueur qui a commencé le duel **ne pioche pas** (aligné sur la règle usuelle à deux joueurs). Avant chaque passe, un port `PriorityActionLegalityPort` peut valider l’état (défaut : aucune contrainte).

```python
from baobab_mtg_rules_engine.engine import TurnManager

tm = TurnManager(game.state)
tm.open_current_step()  # chaîne UNTAP → UPKEEP, ouvre la priorité
tm.pass_priority()      # à répéter côté interface / script
```

Le mana résiduel modélisé sur `PlayerState.floating_mana` est vidé lors du nettoyage, avec événement `FLOATING_MANA_CLEARED` dans le journal.

## Actions légales (périmètre supporté)

Le paquet `baobab_mtg_rules_engine.actions` décrit les **actions atomiques** reconnues (passe, terrain, sort simple, capacité activée simple, déclaration d’attaquants / bloqueurs). Le service `LegalActionService` calcule une **liste triée et déterministe** pour le joueur qui **détient la priorité**, à partir d’un `CardGameplayPort` (par ex. `InMemoryCardCatalogAdapter`).

- **Timing rituel** (terrain, rituel) : principale pré- ou post-combat du joueur **actif**, **pile vide**.
- **Instant** : autorisé avec la priorité même si la pile n’est pas vide (modèle simplifié).
- **Combat** : attaquants / bloqueurs avec **force et endurance** catalogue strictement positives ; **au plus un bloqueur par attaquant** ; déclarations validées par `AttackerDeclarationService` et `BlockerDeclarationService`.
- **Application** : `apply_action` recalcule l’ensemble légal puis refuse toute action absente (`IllegalGameActionError`) avant mutation ; la passe délègue à `TurnManager.pass_priority()`.

```python
from baobab_mtg_rules_engine.actions import CastSpellAction, PassPriorityAction
from baobab_mtg_rules_engine.catalog import InMemoryCardCatalogAdapter
from baobab_mtg_rules_engine.engine import LegalActionService, TurnManager

rules = InMemoryCardCatalogAdapter(
    frozenset({"forest", "bolt"}),
    land_keys=frozenset({"forest"}),
    instant_spell_keys=frozenset({"bolt"}),
    spell_mana_cost_by_key={"bolt": 1},
)
svc = LegalActionService()
# state : GameState avec priorité et mains renseignées ; tm : TurnManager(state)
legal = svc.compute_legal_actions(state, rules, acting_player_index=state.priority_player_index)
if PassPriorityAction() in legal:
    svc.apply_action(state, rules, state.priority_player_index, PassPriorityAction(), tm)
```

Les comportements non modélisés doivent être signalés par les adaptateurs ou par `IllegalGameActionError`, sans mutation implicite.

## Pile, lancement et résolution de sorts (périmètre simple)

Les modules `baobab_mtg_rules_engine.casting`, `baobab_mtg_rules_engine.stack` et `baobab_mtg_rules_engine.targeting` couvrent un sous-ensemble **explicite** : coût mana entier générique, cibles « joueur » ou « créature au champ », pas de coûts alternatifs ni de modalités complexes.

- **`SpellCastService.cast_spell`** : vérifie la carte en main, le timing, le mana flottant et les cibles ; paie le coût ; place un `SpellOnStack` sur la pile et attache un `StackObject` consultable via `GameState.get_stack_object_view`.
- **`StackResolutionService.resolve_top`** : retire le **dernier** objet empilé (LIFO) ; si les cibles ne sont plus légales, le sort **fizzle** (défausse, `SPELL_FIZZLED`) ; sinon effet minimal selon le catalogue (créature → permanent sur le champ du contrôleur, sort de dégâts joueur → `apply_damage` puis défausse).
- **`TargetValidator`** : import direct depuis `baobab_mtg_rules_engine.targeting.target_validator` si besoin (le paquet `targeting` n’exporte que `SimpleTarget` pour éviter les imports circulaires).

```python
from baobab_mtg_rules_engine.casting.spell_cast_service import SpellCastService
from baobab_mtg_rules_engine.stack.stack_resolution_service import StackResolutionService

# rules : InMemoryCardCatalogAdapter avec clés rituel / instant, coûts et spell_target_kind
stack_id = SpellCastService().cast_spell(
    state,
    rules,
    caster_player_index=0,
    spell_hand_object_id=hand_card_id,
    targets=(),
)
StackResolutionService().resolve_top(state, rules)
```

## Combat simplifié, ABS et fin de partie

Le paquet `baobab_mtg_rules_engine.combat` et `StateBasedActionService` couvrent un **duel minimal** : pas de piétinement, pas de plusieurs bloqueurs sur le même attaquant, pas de prévention / remplacement avancés.

- **`CombatService.resolve_combat_damage_step`** : à l’étape `COMBAT_DAMAGE`, attaquant seul inflige sa **force** en dégâts au joueur défenseur ; avec un bloqueur, **échange** de blessures marquées (`Permanent.marked_damage`) selon les forces catalogue.
- **`StateBasedActionService.apply_all`** : envoie en défausse les créatures dont les blessures marquées sont **≥ endurance** ; enregistre la **défaite** d’un joueur à 0 PV ou moins (ou **match nul** si les deux sont à 0 ou moins). À appeler après les dégâts de combat (ou après d’autres sources de dégâts si vous modélisez la fin de partie ainsi).
- **`TurnManager(..., rules=catalog)`** : à l’entrée en `COMBAT_DAMAGE`, enchaîne résolution des blessures puis `apply_all` si un `CardGameplayPort` est fourni ; à l’étape **pioche**, une bibliothèque vide déclenche `record_player_defeat(..., reason="library")`. En **nettoyage**, les blessures marquées sur le champ sont effacées.

```python
from baobab_mtg_rules_engine.combat.combat_service import CombatService
from baobab_mtg_rules_engine.engine import StateBasedActionService, TurnManager

# state en COMBAT_DAMAGE avec attaquants / bloqueurs déjà déclarés ; rules avec P/T
CombatService().resolve_combat_damage_step(state, rules)
StateBasedActionService().apply_all(state, rules)
# vainqueur : state.winner_player_index ; match nul : state.is_draw_game
```

## Scénarios, replay et observabilité

Les modules `baobab_mtg_rules_engine.scenarios`, `replay` et `observability` servent aux **tests de non-régression**, au **debug** et à une **simulation reproductible** sans persistance ni UI.

- **`ScenarioBuilder`** : fabrique un `ScenarioContext` (état, alias stables, `TurnManager`, `LegalActionService`) de façon déterministe.
- **`RecordedGameAction`** : décrit une action par un **genre** et des paramètres (références d’objets = **alias** résolus au replay).
- **`GameReplayService`** : `replay_all` / `apply_step` ; helpers d’assertion sur la **trace d’événements** et le déterminisme entre deux rejouages.
- **`GameStateInspector`** : `event_trace_tuple` (comparaisons stables), `format_events`, `snapshot_summary`.

Le périmètre exact (supporté / non supporté) est détaillé dans `docs/features/08_scenarios_replay_and_observability.md`. Une démonstration minimale : `examples/replay_minimal_example.py`.

```python
from baobab_mtg_rules_engine.catalog import InMemoryCardCatalogAdapter
from baobab_mtg_rules_engine.domain.step import Step
from baobab_mtg_rules_engine.domain.turn_state import TurnState
from baobab_mtg_rules_engine.observability.game_state_inspector import GameStateInspector
from baobab_mtg_rules_engine.replay.game_replay_service import GameReplayService
from baobab_mtg_rules_engine.replay.recorded_game_action import RecordedGameAction
from baobab_mtg_rules_engine.scenarios.scenario_builder import ScenarioBuilder

rules = InMemoryCardCatalogAdapter(frozenset({"forest"}), land_keys=frozenset({"forest"}))
ctx = (
    ScenarioBuilder(rules)
    .with_two_player_game()
    .with_turn_state(TurnState(0, 1, Step.MAIN_PRECOMBAT))
    .with_priority_player(0)
    .add_card_in_hand(0, "forest", alias="f1")
    .build()
)
GameReplayService().replay_all(ctx, (RecordedGameAction.play_land(object_alias="f1"),))
print(GameStateInspector.event_trace_tuple(ctx.state))
```

Les séquences invalides lèvent `ReplaySequenceError` (dérivée de `ValidationException`).

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
- Feature replay / scénarios : `docs/features/08_scenarios_replay_and_observability.md`
- Journal de développement : `docs/dev_diary.md`
- Historique des versions : `CHANGELOG.md`

## Contribution

- Branches de fonctionnalité : `feature/<nom>`
- Commits : [Conventional Commits](https://www.conventionalcommits.org/)
- Tests et outils de qualité doivent passer avant fusion sur `main`

## Licence

Voir la métadonnée `license` dans `pyproject.toml` et les conventions du dépôt Baobab.
