
# Feature 13 — Effets continus et modificateurs de base

## Objectif

Introduire un premier système propre pour les effets continus simples nécessaires à un moteur crédible : +X/+Y temporaires, gain/perte de capacités simples, changement de type/couleur très limité si retenu.

## Branche

`feature/13-continuous-effects-and-basic-modifiers`

## Périmètre

- modèle d’effet continu avec durée : until end of turn, while on battlefield, static local effect
- modification simple de force/endurance
- ajout/retrait de capacités simples utiles au combat
- nettoyage en fin de tour des effets temporaires
- inspection claire de l’état dérivé

## Hors périmètre

- système complet de layers Magic
- timestamps complexes et dépendances avancées

## Critères d’acceptation

- un boost jusqu’à la fin du tour fonctionne réellement
- l’état inspectable expose les caractéristiques dérivées correctement
- la fin de tour nettoie les effets temporaires

## Exigences transverses

- Documentation mise à jour.
- Tests unitaires et scénarios de non-régression.
- Aucune régression sur le périmètre déjà supporté.
