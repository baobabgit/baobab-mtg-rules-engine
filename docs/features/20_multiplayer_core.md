
# Feature 20 — Noyau multijoueur

## Objectif

Étendre le moteur du duel vers un multijoueur générique minimal : ordre du tour, priorité, APNAP, élimination d’un joueur et effets globaux simples.

## Branche

`feature/20-multiplayer-core`

## Périmètre

- game state pour plus de deux joueurs
- ordre de tour généralisé
- APNAP pour triggers et choix ordonnés simples
- défaite et sortie de partie d’un joueur en multijoueur
- compatibilité avec la pile, les triggers et le replay

## Hors périmètre

- formats d’équipe avancés
- portée d’influence limitée

## Critères d’acceptation

- une partie à 3 ou 4 joueurs peut être simulée avec priorité correcte
- les triggers et la résolution respectent un ordre APNAP documenté
- la sortie d’un joueur ne casse pas l’état

## Exigences transverses

- Documentation mise à jour.
- Tests unitaires et scénarios de non-régression.
- Aucune régression sur le périmètre déjà supporté.
