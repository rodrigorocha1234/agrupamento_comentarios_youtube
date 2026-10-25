"""Motor de processamento tabular vetorizado baseado em Polars."""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import final

import polars as pl

from app.dominio_contratos.modelos_dados import TipoDadoJson
from app.processamento_dados.interpretador_dsl import (
    ErroOperadorDslDesconhecido,
    InterpretadorDsl,
)


@final
class MotorPolars:
    """Aplica expressões vetorizadas nativas em DataFrames Polars através da DSL declarativa."""

    def __init__(self, validador_dsl: InterpretadorDsl | None = None) -> None:
        self._dsl = validador_dsl or InterpretadorDsl()

    def selecionar_colunas(
        self, dados: pl.DataFrame, colunas: Sequence[str]
    ) -> pl.DataFrame:
        """Filtra as colunas solicitadas existentes no DataFrame."""
        colunas_validas = [c for c in colunas if c in dados.columns]
        return dados.select(colunas_validas)

    def aplicar_filtros(
        self,
        dados: pl.DataFrame,
        condicoes: Sequence[Mapping[str, TipoDadoJson]],
        combinacao: str = "and",
    ) -> pl.DataFrame:
        """Aplica filtros declarativos via expressões nativas do Polars."""
        if not condicoes or dados.height == 0:
            return dados.clone()

        expressoes: list[pl.Expr] = []
        for cond in condicoes:
            coluna = str(cond.get("coluna", ""))
            operador = str(cond.get("operador", ""))
            valor = cond.get("valor")

            self._dsl.validar_operador_filtro(operador)
            if coluna not in dados.columns:
                continue

            expr = self._construir_expressao_filtro(coluna, operador, valor)
            expressoes.append(expr)

        if not expressoes:
            return dados.clone()

        if combinacao.lower() == "or":
            filtro_composto = expressoes[0]
            for e in expressoes[1:]:
                filtro_composto = filtro_composto | e
        else:
            filtro_composto = expressoes[0]
            for e in expressoes[1:]:
                filtro_composto = filtro_composto & e

        return dados.filter(filtro_composto)

    def criar_atributo(
        self,
        dados: pl.DataFrame,
        nome: str,
        tecnica: str,
        origem: str,
        valor: float | None = None,
        timestamp_referencia: int | None = None,
    ) -> pl.DataFrame:
        """Cria uma nova coluna vetorizada no Polars."""
        self._dsl.validar_operador_transformacao(tecnica)
        if origem not in dados.columns:
            return dados.clone()

        col_origem = pl.col(origem)

        if tecnica == "dividir_constante":
            divisor = float(valor or 1.0)
            return dados.with_columns((col_origem / divisor).alias(nome))
        elif tecnica == "multiplicar_constante":
            fator = float(valor or 1.0)
            return dados.with_columns((col_origem * fator).alias(nome))
        elif tecnica == "log1p":
            return dados.with_columns(
                (col_origem.clip(lower_bound=0.0) + 1.0).log().alias(nome)
            )
        elif tecnica == "converter_dias_desde_referencia":
            ref = timestamp_referencia or int(datetime.now(UTC).timestamp())
            dias_expr = (pl.lit(ref) - col_origem).clip(lower_bound=0.0) / 86400.0
            return dados.with_columns(dias_expr.alias(nome))

        return dados.clone()

    def _construir_expressao_filtro(
        self, coluna: str, operador: str, valor: TipoDadoJson
    ) -> pl.Expr:
        """Mapeia operador para expressão nativa pl.col."""
        c = pl.col(coluna)
        if operador == "igual":
            return c == pl.lit(valor)
        elif operador == "diferente":
            return c != pl.lit(valor)
        elif operador == "maior":
            return c > pl.lit(float(str(valor)))
        elif operador == "maior_igual":
            return c >= pl.lit(float(str(valor)))
        elif operador == "menor":
            return c < pl.lit(float(str(valor)))
        elif operador == "menor_igual":
            return c <= pl.lit(float(str(valor)))
        elif (
            operador == "entre" and isinstance(valor, (list, tuple)) and len(valor) == 2
        ):
            v0 = float(str(valor[0]))
            v1 = float(str(valor[1]))
            return (c >= pl.lit(v0)) & (c <= pl.lit(v1))
        elif operador == "pertence" and isinstance(valor, (list, tuple, set)):
            return c.is_in(list(valor))
        raise ErroOperadorDslDesconhecido(f"Operador '{operador}' inválido.")
