
# Feature 17 — Ciblage avancé, multi-cibles et sorts modaux simples

## Objectif

Faire passer le ciblage du moteur d’un modèle très simple à un modèle capable de gérer plusieurs cibles, des contraintes par rôle de cible, et des modes simples.

## Branche

`feature/17-advanced-targeting-and-modal-support`

## Périmètre

- descripteurs de cibles multiples avec cardinalité et rôle
- validation partielle/totale de légalité à la résolution
- sorts ou capacités avec deux cibles distinctes simples
- modes simples exclusifs choisis au lancement
- replay/scenarios mis à jour pour sérialiser ces choix

## Hors périmètre

- entwine, strive, replicate et coûts variables complexes

## Critères d’acceptation

- un objet peut demander deux cibles distinctes
- le moteur sait ce qui se résout si une partie des cibles devient illégale
- un sort modal simple choisit son mode au cast et reste déterministe en replay

## Exigences transverses

- Documentation mise à jour.
- Tests unitaires et scénarios de non-régression.
- Aucune régression sur le périmètre déjà supporté.
