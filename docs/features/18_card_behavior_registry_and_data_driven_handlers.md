
# Feature 18 — Registre de comportements de cartes et handlers pilotés par données

## Objectif

Rendre le moteur extensible sans coder la logique des cartes partout : registre de comportements, mapping depuis le catalogue et handlers génériques/spécifiques encadrés.

## Branche

`feature/18-card-behavior-registry-and-data-driven-handlers`

## Périmètre

- registry central des comportements supportés
- liaison propre entre métadonnées catalogue et handlers runtime
- séparation nette noyau générique vs comportements spécifiques supportés
- refus explicite des comportements non couverts
- documentation des familles de comportements supportées

## Hors périmètre

- couverture de toutes les cartes Magic
- DSL complet de scripting si cela explose le périmètre

## Critères d’acceptation

- ajouter une nouvelle famille de carte supportée ne nécessite pas de toucher partout dans le moteur
- les cartes non supportées échouent proprement avec exception projet adaptée
- le README et les docs listent les familles de comportements réellement supportées

## Exigences transverses

- Documentation mise à jour.
- Tests unitaires et scénarios de non-régression.
- Aucune régression sur le périmètre déjà supporté.
