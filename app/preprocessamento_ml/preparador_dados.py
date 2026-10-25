"""Preparador de dados para segregação estrita entre matriz de treino e metadados de consulta."""

from typing import Final

import numpy as np
import pandas as pd

from app.conf_yaml import ConfigAtributosInfo
from app.excecoes import ErroPreprocessamento

COLUNAS_BOOLEANAS_CONHECIDAS: Final[set[str]] = {"voted_up", "recomendado"}


class PreparadorDados:
    """Higieniza e divide os dados da camada Silver em matriz de treino e metadados de rastreabilidade."""

    def __init__(self, config_atributos: ConfigAtributosInfo) -> None:
        self._config = config_atributos

    def preparar(self, dados: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Segrega os atributos de treino e preserva metadados/identificadores para auditoria.

        Args:
            dados: DataFrame da camada Silver.

        Retorna:
            Tupla contendo:
                1. df_treino: DataFrame estritamente numérico contendo apenas as variáveis autorizadas.
                2. df_metadados: DataFrame contendo identificadores e textos de avaliação originais.

        Raises:
            ErroPreprocessamento: Se nenhum atributo de treino estiver presente ou se identificadores
                                  foram indevidamente incluídos no conjunto de treino.
        """
        if dados.empty:
            raise ErroPreprocessamento("O conjunto de dados da camada Silver está vazio.")

        identificadores_config = set(self._config.identificadores)
        colunas_avaliacao_config = set(self._config.avaliacao.colunas)

        # Regra de ouro: Identificadores e texto jamais compõem o conjunto de treino
        colunas_treino_candidatas = list(self._config.treino.colunas)
        colunas_treino_finais: list[str] = []

        for col in colunas_treino_candidatas:
            if col in identificadores_config:
                continue
            if not self._config.texto.incluir_no_treino and (
                col in colunas_avaliacao_config or col == "review"
            ):
                continue
            if col in dados.columns:
                colunas_treino_finais.append(col)

        if not colunas_treino_finais:
            raise ErroPreprocessamento(
                "Nenhuma coluna de treino válida encontrada nos dados. "
                f"Colunas requeridas: {self._config.treino.colunas}, presentes: {list(dados.columns)}"
            )

        # 1. Montagem do DataFrame de treino
        df_treino = dados[colunas_treino_finais].copy()

        # Converte booleanos em 0.0 / 1.0 numérico
        for col in colunas_treino_finais:
            if col in COLUNAS_BOOLEANAS_CONHECIDAS or df_treino[col].dtype == bool:
                df_treino[col] = df_treino[col].astype(float)
            else:
                serie_num = pd.to_numeric(df_treino[col], errors="coerce")
                if isinstance(serie_num, pd.Series):
                    df_treino[col] = serie_num
                else:
                    df_treino[col] = df_treino[col].astype(float)

        # Garante tipo float64 para todos os atributos de treino
        df_treino_final = pd.DataFrame(df_treino.astype(np.float64))

        # 2. Montagem do DataFrame de metadados (para consulta humana e relatórios)
        colunas_metadados = [
            c
            for c in dados.columns
            if c in identificadores_config or c in colunas_avaliacao_config or c == "review"
        ]
        df_metadados_final = (
            pd.DataFrame(dados.loc[:, colunas_metadados])
            if colunas_metadados
            else pd.DataFrame(index=dados.index)
        )

        return df_treino_final, df_metadados_final
