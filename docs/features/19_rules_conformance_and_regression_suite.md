
# Feature 19 — Conformité aux règles et suite de scénarios de non-régression

## Objectif

Durcir le moteur par une vraie campagne de conformité métier fondée sur les règles ciblées et des scénarios déterministes couvrant les invariants du jeu.

## Branche

`feature/19-rules-conformance-and-regression-suite`

## Périmètre

- matrice de conformité règle -> test -> module
- scénarios de référence pour priorité, pile, combat, triggers, SBA, ciblage, zone changes
- fixtures de régression lisibles et versionnées
- audit des écarts restants explicitement documentés

## Hors périmètre

- certification exhaustive de toutes les CR Magic

## Critères d’acceptation

- une matrice de couverture métier existe dans docs/
- les scénarios critiques sont rejouables en CI
- les limites restantes sont listées noir sur blanc

## Exigences transverses

- Documentation mise à jour.
- Tests unitaires et scénarios de non-régression.
- Aucune régression sur le périmètre déjà supporté.
