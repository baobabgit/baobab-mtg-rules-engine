"""Exception racine pour toutes les erreurs du moteur de règles."""


class BaobabMtgRulesEngineException(Exception):
    """Exception de base pour le moteur ``baobab-mtg-rules-engine``.

    Toute erreur métier ou technique spécifique au moteur doit hériter
    de cette classe afin de permettre un filtrage homogène côté appelant.

    :param message: Description lisible de l'erreur.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self._message: str = message

    @property
    def message(self) -> str:
        """Message d'erreur associé à l'exception.

        :return: Texte décrivant l'erreur.
        """
        return self._message
