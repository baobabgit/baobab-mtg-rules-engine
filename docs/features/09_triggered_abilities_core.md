# Feature 09 — Capacités déclenchées — noyau complet

## Objectif

Implémenter un noyau déterministe de capacités déclenchées simples :
- détection sur événements moteur,
- file d’attente explicite,
- mise sur la pile au bon moment (après SBA, avant retour de priorité),
- résolution/fizzle avec journal dédié.

## Composants ajoutés

| Module | Rôle |
|--------|------|
| `domain.triggered_ability_definition` | Définition déclarative d’un trigger simple (kind, effet, cible, amount). |
| `domain.pending_triggered_ability` | Entrée de file d’attente d’un trigger détecté mais pas encore empilé. |
| `domain.triggered_ability_stack_object` | Vue métier d’une capacité déclenchée sur la pile. |
| `engine.trigger_detection_service` | Scan incrémental des événements + fallback begin-step depuis l’état courant. |
| `stack.triggered_ability_resolution_service` | Résolution des capacités déclenchées, fizzle si cible illégale. |
| `engine.turn_manager` | Orchestration complète SBA → triggers → pile → priorité/résolution. |

## Événements moteur ajoutés

- `TRIGGER_DETECTED`
- `TRIGGER_QUEUED`
- `TRIGGER_STACKED`
- `TRIGGER_RESOLVED`
- `TRIGGER_FIZZLED`

## Périmètre supporté

### Déclencheurs

- `etb_self`
- `dies_self`
- `cast_self`
- `begin_step` (scope `you` ou `any`)
- `draw_you`
- `combat_damage_to_player_self`

### Effets

- `damage_opponent`
- `damage_player` (cible joueur)
- `destroy_target_creature` (cible créature)
- `draw_cards`

### Cibles

- `none`
- `player`
- `creature`

## Ordonnancement et priorité

- Les triggers détectés passent d’abord en file (`PendingTriggeredAbility`), puis sont empilés en bloc.
- En duel, l’ordre d’empilement est déterministe avec APNAP simplifié :
  - contrôleur actif d’abord,
  - puis non-actif,
  - tie-break par `pending_trigger_id`.
- La priorité est réattribuée au joueur actif **après** empilement des triggers.
- Un trigger n’est pas mis sur la pile pendant la résolution d’un autre objet ; il est empilé à la prochaine fenêtre correcte.

## Résolution / fizzle

- À la résolution d’un trigger ciblé, la légalité est revalidée.
- Si la cible est devenue illégale : `TRIGGER_FIZZLED`, aucun effet appliqué.
- Sinon : effet appliqué puis `TRIGGER_RESOLVED`.

## Intégration catalogue gameplay

Le `CardGameplayPort` expose désormais :
- `triggered_ability_definitions(catalog_key) -> tuple[TriggeredAbilityDefinition, ...]`

`InMemoryCardCatalogAdapter` supporte ces définitions via :
- `triggered_abilities_by_key={...}`

`BaobabMtgCatalogAdapter` refuse encore ce point d’extension via `UnsupportedRuleException`.

## Couverture de tests

- Intégration flux déclenché : `tests/.../engine/test_triggered_ability_flow.py`
  - trigger sur cast,
  - trigger ETB,
  - trigger dies,
  - trigger upkeep APNAP,
  - fizzle sur cible illégale.
- Unitaire détection : `tests/.../engine/test_trigger_detection_service.py`
- Unitaire résolution : `tests/.../stack/test_triggered_ability_resolution_service.py`
- Validation définition : `tests/.../domain/test_triggered_ability_definition.py`


# Feature 09 — Capacités déclenchées — noyau complet

## Objectif

Implémenter un vrai système de capacités déclenchées simples : détection sur événements, file d’attente, mise sur la pile au bon moment, contrôle APNAP simplifié en duel, résolution et tests de non-régression.

## Branche

`feature/09-triggered-abilities-core`

## Périmètre

- détection des triggers à partir du journal ou d’un bus d’événements de jeu
- représentation explicite d’un trigger en attente puis d’une capacité sur la pile
- mise sur la pile lorsque les SBA ont été vérifiées et avant ré-attribution de la priorité
- support initial des triggers simples : ETB, dies, cast, begin step, draw, combat damage to player
- contrôleur correct du trigger et ordre déterministe en duel
- journal d’événements explicite pour trigger detected / queued / stacked / resolved / fizzled si cible illégale

## Hors périmètre

- triggers multijoueurs complexes
- may abilities avec interface utilisateur riche
- interactions avancées type delayed triggers imbriqués complexes au-delà du nécessaire

## Critères d’acceptation

- une capacité déclenchée simple est détectée au bon événement et n’est pas oubliée
- elle est mise sur la pile au bon moment, pas pendant la résolution d’un autre objet
- la priorité revient au bon joueur après mise sur la pile
- les cibles éventuelles sont validées au moment voulu
- les tests couvrent ETB, dies, upkeep trigger et trigger sur cast

## Exigences transverses

- Documentation mise à jour.
- Tests unitaires et scénarios de non-régression.
- Aucune régression sur le périmètre déjà supporté.
