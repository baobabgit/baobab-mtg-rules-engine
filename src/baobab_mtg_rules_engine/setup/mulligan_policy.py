"""Politique de mulligan documentée pour le setup."""


class MulliganPolicy:
    """Mulligan parisien simplifié pour le périmètre moteur.

    Règle retenue (document MTG classique, simplifiée ici) :

    - La taille de la main ouvrante est ``7``.
    - Chaque mulligan : la main actuelle retourne dans la bibliothèque,
      celle-ci est mélangée, puis le joueur pioche une main de taille
      ``7 - n`` où ``n`` est le nombre de mulligans déjà pris par ce joueur
      dans cette phase de setup.
    - Aucune action de scry n'est modélisée à ce stade.

    L'ordre des décisions est externe au moteur : voir :class:`MulliganChoicePort`.
    """

    OPENING_HAND: int = 7

    def hand_size_after_mulligans(self, mulligans_taken: int) -> int:
        """Calcule la taille de la main après ``mulligans_taken`` mulligans.

        :param mulligans_taken: Nombre de mulligans déjà effectués par le joueur.
        :return: Taille de la prochaine main (``0`` si le plafond est atteint).
        """
        if mulligans_taken < 0:
            msg = "mulligans_taken ne peut pas être négatif."
            raise ValueError(msg)
        return max(0, self.OPENING_HAND - mulligans_taken)
