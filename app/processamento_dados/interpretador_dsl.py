"""Interpretador seguro de DSL declarativa para filtros e transformações tabulares sem eval/exec."""

from typing import final


class ErroOperadorDslDesconhecido(Exception):
    """Exceção levantada quando a regra YAML especificar um operador não registrado."""


@final
class InterpretadorDsl:
    """Valida e normaliza operadores de filtros e criação de atributos declarativos."""

    _OPERADORES_FILTRO = frozenset(
        {
            "igual",
            "diferente",
            "maior",
            "maior_igual",
            "menor",
            "menor_igual",
            "entre",
            "pertence",
        }
    )

    _OPERADORES_TRANSFORMACAO = frozenset(
        {
            "dividir_constante",
            "multiplicar_constante",
            "soma",
            "subtrai",
            "log1p",
            "converter_dias_desde_referencia",
        }
    )

    def validar_operador_filtro(self, operador: str) -> None:
        """Verifica se o operador de filtro é suportado."""
        if operador not in self._OPERADORES_FILTRO:
            raise ErroOperadorDslDesconhecido(
                f"Operador de filtro '{operador}' não suportado pela DSL."
            )

    def validar_operador_transformacao(self, tecnica: str) -> None:
        """Verifica se a técnica de transformação é suportada."""
        if tecnica not in self._OPERADORES_TRANSFORMACAO:
            raise ErroOperadorDslDesconhecido(
                f"Técnica de transformação '{tecnica}' não suportada pela DSL."
            )
