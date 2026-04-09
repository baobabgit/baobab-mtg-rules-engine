
# Feature 10 — Capacités activées — coûts, pile et résolution

## Objectif

Passer d’une activation symbolique à un vrai cycle d’activation des capacités activées simples : légalité, coûts, ciblage, mise sur la pile, résolution et effets.

## Branche

`feature/10-activated-abilities-stack-and-costs`

## Périmètre

- modèle de capacité activée indépendante du simple événement journalisé
- coûts simples supportés : mana générique, engagement, sacrifice simple, coût de vie simple si retenu
- timing et restrictions d’activation
- ciblage simple joueur / créature / permanent selon métadonnées gameplay
- mise sur la pile via AbilityOnStack et résolution unifiée
- capacités de mana simples si tu peux les traiter proprement hors pile ; sinon refus explicite documenté

## Hors périmètre

- capacités de loyauté complètes
- coûts alternatifs ou imbriqués complexes
- copie de capacités

## Critères d’acceptation

- une capacité activée simple peut être listée comme action légale
- son coût est payé correctement et atomiquement
- elle va sur la pile puis se résout via la stack commune
- une cible devenue illégale empêche la résolution si les règles simplifiées l’exigent
- les tests couvrent au moins une capacité de ping, une capacité avec tap cost et une capacité de sacrifice

## Exigences transverses

- Documentation mise à jour.
- Tests unitaires et scénarios de non-régression.
- Aucune régression sur le périmètre déjà supporté.
