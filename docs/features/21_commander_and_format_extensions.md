
# Feature 21 — Extensions de format : Commander

## Objectif

Ajouter un premier format avancé à forte valeur, Commander, sans casser le noyau : zone de commandement, commandant, identité couleur, taxe de commandant, dégâts de commandant.

## Branche

`feature/21-commander-and-format-extensions`

## Périmètre

- zone de commandement
- setup Commander et validation de deck
- commandeur désigné par joueur
- cast depuis command zone avec taxe croissante simple
- suivi des blessures de commandant et condition de défaite associée

## Hors périmètre

- partenaires complexes, initiative, monarch au complet
- Commander multijoueur avec toutes les subtilités politiques dès la première itération

## Critères d’acceptation

- un setup Commander simple fonctionne
- la taxe de commandant est appliquée correctement
- les dégâts de commandant sont suivis et peuvent faire perdre la partie

## Exigences transverses

- Documentation mise à jour.
- Tests unitaires et scénarios de non-régression.
- Aucune régression sur le périmètre déjà supporté.
