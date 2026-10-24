from collections.abc import Sequence
from typing import final

import pandas as pd


@final
class SeletorColunasTreinamento:
    """Extrai matrizes de treino sem identificadores ou texto de reviews."""

    _COLUNAS_PROIBIDAS_TREINO = frozenset(
        {
            "appid",
            "recommendationid",
            "steamid",
            "review_texto",
            "developer_response",
            "language",
        }
    )

    def extrair_matriz_treino(
        self, dados: pd.DataFrame, colunas_desejadas: Sequence[str]
    ) -> pd.DataFrame:
        """Garante que apenas colunas numéricas permitidas componham a matriz X."""
        colunas_filtradas = [
            c
            for c in colunas_desejadas
            if c in dados.columns and c not in self._COLUNAS_PROIBIDAS_TREINO
        ]
        if not colunas_filtradas:
            raise ValueError(
                "Nenhuma coluna válida de treinamento foi encontrada no DataFrame."
            )

        matriz_x = pd.DataFrame(dados.loc[:, colunas_filtradas])
        # Converte para float numérico estrito
        for col in list(matriz_x.columns):
            serie_col = matriz_x[col]
            if isinstance(serie_col, pd.Series):
                convertido = pd.to_numeric(serie_col, errors="coerce")
                if isinstance(convertido, pd.Series):
                    matriz_x[col] = convertido.fillna(0.0)
                else:
                    matriz_x[col] = 0.0
            else:
                matriz_x[col] = 0.0
        return matriz_x

    def extrair_metadados_avaliacao(
        self, dados: pd.DataFrame, colunas_avaliacao: Sequence[str]
    ) -> pd.DataFrame:
        """Extrai atributos para auditoria, interpretação de negócio e rotulagem."""
        colunas_existentes = [c for c in colunas_avaliacao if c in dados.columns]
        return pd.DataFrame(dados.loc[:, colunas_existentes])
