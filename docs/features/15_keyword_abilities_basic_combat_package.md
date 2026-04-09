
# Feature 15 — Capacités mot-clé de base pour un combat crédible

## Objectif

Étendre le combat simplifié avec un paquet ciblé de capacités mot-clé fondamentales : haste, vigilance, flying, reach, first strike, double strike, trample, deathtouch, lifelink.

## Branche

`feature/15-keyword-abilities-basic-combat-package`

## Périmètre

- restrictions/permissions d’attaque et de blocage liées aux capacités
- ordre de blessures first strike / normal damage
- piétinement simple sur assignation à joueur défenseur
- deathtouch et lifelink en version correctement intégrée aux dégâts
- inspection des capacités pertinentes pendant combat

## Hors périmètre

- banding, protection complète, shadow, menace complexe multi-bloqueurs

## Critères d’acceptation

- flying/reach impactent bien les bloqueurs légaux
- first strike/double strike modifient la séquence de combat
- trample transmet le surplus de dégâts au joueur
- lifelink et deathtouch sont appliqués dans le bon pipeline de dégâts

## Exigences transverses

- Documentation mise à jour.
- Tests unitaires et scénarios de non-régression.
- Aucune régression sur le périmètre déjà supporté.
