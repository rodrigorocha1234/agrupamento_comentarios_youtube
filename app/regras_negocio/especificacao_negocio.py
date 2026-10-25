"""Padrão GoF Specification e Composite para regras de negócio declarativas."""

from collections.abc import Mapping, Sequence
from typing import Protocol, final, runtime_checkable

from app.dominio_contratos.modelos_dados import TipoDadoJson, TipoValorEscalar


@runtime_checkable
class EspecificacaoNegocio(Protocol):
    """Protocolo GoF Specification para predicados avaliáveis sobre contextos analíticos."""

    def satisfeita_por(self, contexto: Mapping[str, TipoValorEscalar]) -> bool:
        """Avalia se o contexto de métricas atende aos critérios da especificação."""
        ...


@final
class EspecificacaoCondicao(EspecificacaoNegocio):
    """Especificação folha que avalia uma condição atômica declarativa."""

    def __init__(self, metrica: str, operador: str, valor_esperado: TipoDadoJson) -> None:
        self._metrica = metrica
        self._operador = operador.lower()
        self._valor_esperado = valor_esperado

    def satisfeita_por(self, contexto: Mapping[str, TipoValorEscalar]) -> bool:
        if self._metrica not in contexto:
            return False

        valor_atual = contexto[self._metrica]
        if valor_atual is None:
            return False

        try:
            if self._operador == "igual":
                return valor_atual == self._valor_esperado
            elif self._operador == "diferente":
                return valor_atual != self._valor_esperado

            # Conversão para avaliação numérica
            v_atual = float(str(valor_atual))

            if (
                self._operador == "entre"
                and isinstance(self._valor_esperado, (list, tuple))
                and len(self._valor_esperado) == 2
            ):
                v_min = float(str(self._valor_esperado[0]))
                v_max = float(str(self._valor_esperado[1]))
                return v_min <= v_atual <= v_max

            # Operadores numéricos escalares
            v_esp = float(str(self._valor_esperado))

            if self._operador == "maior":
                return v_atual > v_esp
            elif self._operador == "maior_igual":
                return v_atual >= v_esp
            elif self._operador == "menor":
                return v_atual < v_esp
            elif self._operador == "menor_igual":
                return v_atual <= v_esp

        except (ValueError, TypeError):
            return False

        return False


@final
class EspecificacaoCompostaAnd(EspecificacaoNegocio):
    """Padrão GoF Composite para conjunção lógica (AND) de especificações."""

    def __init__(self, especificacoes: Sequence[EspecificacaoNegocio]) -> None:
        self._especificacoes = list(especificacoes)

    def satisfeita_por(self, contexto: Mapping[str, TipoValorEscalar]) -> bool:
        return all(esp.satisfeita_por(contexto) for esp in self._especificacoes)


@final
class EspecificacaoCompostaOr(EspecificacaoNegocio):
    """Padrão GoF Composite para disjunção lógica (OR) de especificações."""

    def __init__(self, especificacoes: Sequence[EspecificacaoNegocio]) -> None:
        self._especificacoes = list(especificacoes)

    def satisfeita_por(self, contexto: Mapping[str, TipoValorEscalar]) -> bool:
        return any(esp.satisfeita_por(contexto) for esp in self._especificacoes)
