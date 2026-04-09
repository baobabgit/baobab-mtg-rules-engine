
# Feature 12 — Choix de résolution et demandes de décision

## Objectif

Ajouter un cadre générique pour les choix requis pendant la résolution : choisir une cible parmi plusieurs, choisir oui/non, choisir un mode simple, choisir l’ordre d’un groupe si nécessaire.

## Branche

`feature/12-resolution-choices-and-decision-requests`

## Périmètre

- abstraction de DecisionRequest / DecisionPort ou équivalent
- intégration avec le moteur sans coupler une UI
- support des choix oui/non et choix d’un objet légal simple
- support des effets “may” simples
- replay/scenarios compatibles avec ces choix

## Hors périmètre

- interface utilisateur
- négociation multijoueur
- choix cachés complexes

## Critères d’acceptation

- le moteur peut demander un choix pendant la résolution sans casser le déterminisme
- les choix sont sérialisables pour le replay
- les tests couvrent au moins une capacité ou un sort avec choix optionnel

## Exigences transverses

- Documentation mise à jour.
- Tests unitaires et scénarios de non-régression.
- Aucune régression sur le périmètre déjà supporté.
