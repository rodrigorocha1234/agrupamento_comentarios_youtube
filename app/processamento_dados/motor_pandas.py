from collections.abc import Mapping, Sequence
from typing import final

import numpy as np
import pandas as pd

from app.processamento_dados.interpretador_dsl import (
    ErroOperadorDslDesconhecido,
    InterpretadorDsl,
)


@final
class MotorPandas:
    """Aplica operações vetorizadas em DataFrames Pandas através da DSL declarativa."""

    def __init__(self, validador_dsl: InterpretadorDsl | None = None) -> None:
        self._dsl = validador_dsl or InterpretadorDsl()

    def selecionar_colunas(
        self, dados: pd.DataFrame, colunas: Sequence[str]
    ) -> pd.DataFrame:
        """Filtra apenas as colunas solicitadas existentes no DataFrame."""
        colunas_validas = [c for c in colunas if c in dados.columns]
        return pd.DataFrame(dados.loc[:, colunas_validas])

    def aplicar_filtros(
        self,
        dados: pd.DataFrame,
        condicoes: Sequence[Mapping[str, object]],
        combinacao: str = "and",
    ) -> pd.DataFrame:
        """Aplica filtros declarativos vetorizados sobre o DataFrame."""
        if not condicoes or dados.empty:
            return dados.copy()

        mascaras: list[np.ndarray] = []
        for cond in condicoes:
            coluna = str(cond.get("coluna", ""))
            operador = str(cond.get("operador", ""))
            valor = cond.get("valor")

            self._dsl.validar_operador_filtro(operador)
            if coluna not in dados.columns:
                continue

            serie_bruta = dados[coluna]
            if not isinstance(serie_bruta, pd.Series):
                continue

            mascara_arr = self._avaliar_condicao(serie_bruta, operador, valor)
            mascaras.append(mascara_arr)

        if not mascaras:
            return dados.copy()

        if combinacao.lower() == "or":
            resultado_mascara = np.logical_or.reduce(mascaras)
        else:
            resultado_mascara = np.logical_and.reduce(mascaras)

        return pd.DataFrame(dados.loc[resultado_mascara])

    def criar_atributo(
        self,
        dados: pd.DataFrame,
        nome: str,
        tecnica: str,
        origem: str,
        valor: float | None = None,
        timestamp_referencia: int | None = None,
    ) -> pd.DataFrame:
        """Cria uma nova coluna vetorizada conforme a técnica declarativa especificada."""
        self._dsl.validar_operador_transformacao(tecnica)
        resultado = dados.copy()

        if origem not in dados.columns:
            return resultado

        serie_origem = resultado[origem]

        if tecnica == "dividir_constante":
            divisor = float(valor or 1.0)
            resultado[nome] = serie_origem / divisor
        elif tecnica == "multiplicar_constante":
            fator = float(valor or 1.0)
            resultado[nome] = serie_origem * fator
        elif tecnica == "log1p":
            serie_positiva = np.maximum(
                np.asarray(serie_origem.values, dtype=np.float64), 0.0
            )
            resultado[nome] = np.log1p(serie_positiva)
        elif tecnica == "converter_dias_desde_referencia":
            ref = timestamp_referencia or int(pd.Timestamp.now().timestamp())
            diferenca_segundos = np.maximum(
                ref - np.asarray(serie_origem.values, dtype=np.float64), 0.0
            )
            resultado[nome] = diferenca_segundos / 86400.0

        return resultado

    def _avaliar_condicao(
        self, serie: pd.Series, operador: str, valor: object
    ) -> np.ndarray:
        """Avalia um operador único de forma vetorizada retornando array booleano."""
        arr_obj = np.asarray(serie.values)

        if operador == "igual":
            return np.asarray(arr_obj == valor, dtype=np.bool_)
        elif operador == "diferente":
            return np.asarray(arr_obj != valor, dtype=np.bool_)
        elif operador == "pertence" and isinstance(valor, (list, tuple, set)):
            return np.asarray(serie.isin(valor).values, dtype=np.bool_)

        # Operadores numéricos
        num_series = pd.to_numeric(serie, errors="coerce")
        if isinstance(num_series, pd.Series):
            arr_num = np.asarray(num_series.values, dtype=np.float64)
        else:
            arr_num = np.zeros(len(serie), dtype=np.float64)

        val_float = float(str(valor)) if not isinstance(valor, (list, tuple)) else 0.0

        if operador == "maior":
            return np.asarray(arr_num > val_float, dtype=np.bool_)
        elif operador == "maior_igual":
            return np.asarray(arr_num >= val_float, dtype=np.bool_)
        elif operador == "menor":
            return np.asarray(arr_num < val_float, dtype=np.bool_)
        elif operador == "menor_igual":
            return np.asarray(arr_num <= val_float, dtype=np.bool_)
        elif (
            operador == "entre" and isinstance(valor, (list, tuple)) and len(valor) == 2
        ):
            v0 = float(valor[0])
            v1 = float(valor[1])
            cond = (arr_num >= v0) & (arr_num <= v1)
            return np.asarray(cond, dtype=np.bool_)

        raise ErroOperadorDslDesconhecido(f"Operador '{operador}' inválido.")
