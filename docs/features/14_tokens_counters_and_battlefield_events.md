
# Feature 14 — Jetons, marqueurs, ETB/LTB et événements de champ de bataille

## Objectif

Ajouter les primitives de jetons et marqueurs pour enrichir le moteur et débloquer beaucoup de cartes simples, avec événements d’arrivée et de sortie du champ de bataille mieux structurés.

## Branche

`feature/14-tokens-counters-and-battlefield-events`

## Périmètre

- représentation d’un token comme objet runtime non carte
- création de jetons simples sur le champ de bataille
- marqueurs +1/+1 et -1/-1 de base
- gestion ETB/LTB suffisamment fiable pour nourrir les triggers simples
- nettoyage des tokens quittant le champ correctement

## Hors périmètre

- copie de tokens complexe
- sagas, planeswalkers, poison, énergie

## Critères d’acceptation

- un effet peut créer un jeton simple
- les marqueurs modifient la P/T effectivement
- les événements ETB/LTB sont traçables et testés

## Exigences transverses

- Documentation mise à jour.
- Tests unitaires et scénarios de non-régression.
- Aucune régression sur le périmètre déjà supporté.
