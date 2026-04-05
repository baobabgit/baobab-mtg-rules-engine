"""Exception levée lorsqu'une validation de légalité ou d'invariant échoue."""

from baobab_mtg_rules_engine.exceptions.baobab_mtg_rules_engine_exception import (
    BaobabMtgRulesEngineException,
)


class ValidationException(BaobabMtgRulesEngineException):
    """Erreur de validation avant toute mutation d'état illégale.

    Les contrôles de légalité doivent précéder les mutations : cette
    exception matérialise l'échec d'une telle validation.

    :param message: Description de la violation détectée.
    :param field_name: Nom logique du champ ou de l'élément en cause, si pertinent.
    """

    def __init__(self, message: str, *, field_name: str | None = None) -> None:
        super().__init__(message)
        self._field_name: str | None = field_name

    @property
    def field_name(self) -> str | None:
        """Nom du champ ou concept validé, si renseigné.

        :return: Identifiant de champ ou ``None``.
        """
        return self._field_name
