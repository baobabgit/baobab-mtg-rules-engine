
# Feature 11 — Sorts ciblés, blessures de sort, destruction et transitions de zone

## Objectif

Compléter le support des éphémères et rituels simples qui ciblent joueurs et créatures, infligent des blessures, détruisent, exilent ou déplacent un objet entre zones simples.

## Branche

`feature/11-targeted-spells-damage-destruction-and-zone-changes`

## Périmètre

- résolution de sorts ciblant une créature sur le champ de bataille
- dégâts de sort à créature et à joueur
- destruction simple d’une créature ciblée
- changements de zone explicites avec nouveaux identifiants runtime quand requis
- fizzle correct si toutes les cibles deviennent illégales
- journal détaillé des transitions de zone

## Hors périmètre

- sorts multi-modes complexes
- effets X avancés
- réanimation complexe hors cas simple explicite

## Critères d’acceptation

- un rituel/éphémère simple de blast peut tuer une créature
- un sort de destruction ciblée envoie correctement au cimetière
- la résolution distingue bien battlefield, graveyard, exile et stack
- les SBA détruisent ensuite les créatures létales survivantes si nécessaire

## Exigences transverses

- Documentation mise à jour.
- Tests unitaires et scénarios de non-régression.
- Aucune régression sur le périmètre déjà supporté.
