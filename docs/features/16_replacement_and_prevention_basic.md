
# Feature 16 — Effets de remplacement et de prévention de base

## Objectif

Introduire une première couche d’effets de remplacement/prévention pour couvrir les cartes simples qui modifient pioche, dégâts, arrivée en jeu ou changements de zone.

## Branche

`feature/16-replacement-and-prevention-basic`

## Périmètre

- pipeline explicite d’événement remplaçable
- prévention simple de dégâts
- remplacement simple “if it would die, exile it instead”
- remplacement simple de draw ou ETB quand utile
- ordre d’application documenté et déterministe dans le périmètre supporté

## Hors périmètre

- gestion exhaustive de tous les cas 614-616
- arbres de choix complexes multijoueurs

## Critères d’acceptation

- un effet de prévention simple modifie bien l’événement de dégâts
- un effet de remplacement de mort vers exil fonctionne
- les tests rendent visible l’ordre d’application choisi

## Exigences transverses

- Documentation mise à jour.
- Tests unitaires et scénarios de non-régression.
- Aucune régression sur le périmètre déjà supporté.
