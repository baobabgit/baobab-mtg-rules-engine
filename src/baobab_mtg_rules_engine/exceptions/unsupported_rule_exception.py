"""Exception levée lorsqu'une règle ou capacité n'est pas encore supportée."""

from baobab_mtg_rules_engine.exceptions.baobab_mtg_rules_engine_exception import (
    BaobabMtgRulesEngineException,
)


class UnsupportedRuleException(BaobabMtgRulesEngineException):
    """Erreur explicite pour tout comportement non implémenté ou hors périmètre.

    Le moteur reste déterministe : une action ou une règle non supportée
    doit échouer de façon claire plutôt qu'avec un comportement implicite.

    :param message: Description de ce qui n'est pas supporté.
    :param rule_reference: Référence optionnelle (ex. numéro de règle CR).
    """

    def __init__(self, message: str, rule_reference: str | None = None) -> None:
        super().__init__(message)
        self._rule_reference: str | None = rule_reference

    @property
    def rule_reference(self) -> str | None:
        """Référence de règle associée, si fournie à la construction.

        :return: Identifiant de règle ou ``None``.
        """
        return self._rule_reference
