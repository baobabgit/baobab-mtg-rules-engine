
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
