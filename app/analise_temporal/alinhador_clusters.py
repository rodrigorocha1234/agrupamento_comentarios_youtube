"""Alinhador de clusters temporais para resolução de permutação de rótulos entre janelas."""

from collections.abc import Mapping
from typing import final

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment


@final
class AlinhadorClustersTemporal:
    """Resolve a permutação de identificadores de clusters entre duas sessões temporais."""

    def calcular_alinhamento(
        self,
        centroides_t0: np.ndarray,
        centroides_t1: np.ndarray,
        ids_t0: list[int] | None = None,
        ids_t1: list[int] | None = None,
    ) -> tuple[dict[int, int], float]:
        """Calcula o mapeamento ótimo de menor distância entre centróides de t1 e t0.

        Retorna o dicionário de mapeamento {id_t1: id_t0_alinhado} e a distância média.
        """
        if centroides_t0.ndim != 2 or centroides_t1.ndim != 2:
            raise ValueError(
                "As matrizes de centróides devem ter exatamente 2 dimensões."
            )

        n_t0, d_t0 = centroides_t0.shape
        n_t1, d_t1 = centroides_t1.shape

        if d_t0 != d_t1:
            raise ValueError(
                f"Incompatibilidade dimensional de atributos: {d_t0} != {d_t1}"
            )

        lista_ids_t0 = ids_t0 if ids_t0 is not None else list(range(n_t0))
        lista_ids_t1 = ids_t1 if ids_t1 is not None else list(range(n_t1))

        # Matriz de custo por distância Euclidiana
        diff = centroides_t1[:, np.newaxis, :] - centroides_t0[np.newaxis, :, :]
        matriz_distancias = np.linalg.norm(diff, axis=2)

        # Resolução ótima por atribuição linear (algoritmo Húngaro / Jonker-Volgenant)
        linhas_t1, colunas_t0 = linear_sum_assignment(matriz_distancias)

        mapeamento: dict[int, int] = {}
        soma_distancias = 0.0

        for r, c in zip(linhas_t1, colunas_t0, strict=False):
            id_origem = lista_ids_t1[int(r)]
            id_destino = lista_ids_t0[int(c)]

            mapeamento[id_origem] = id_destino
            soma_distancias += float(matriz_distancias[r, c])

        # Trata clusters adicionais que não puderam ser pareados
        for idx_t1 in range(n_t1):
            cand_id = lista_ids_t1[idx_t1]
            if cand_id not in mapeamento:
                mapeamento[cand_id] = cand_id

        distancia_media = (
            soma_distancias / float(len(linhas_t1)) if len(linhas_t1) > 0 else 0.0
        )
        return mapeamento, distancia_media

    def aplicar_alinhamento_dataframe(
        self,
        dados_t1: pd.DataFrame,
        mapeamento: Mapping[int, int],
        coluna_cluster_origem: str = "cluster_id",
        coluna_cluster_alinhado: str = "cluster_id_alinhado",
    ) -> pd.DataFrame:
        """Aplica o mapeamento de rótulos em nova coluna sem sobrescrever a original."""
        resultado = dados_t1.copy()
        if coluna_cluster_origem not in resultado.columns:
            return resultado

        def _mapear(cid: str | float | None) -> int:
            try:
                c_int = int(str(cid))
                return mapeamento.get(c_int, c_int)
            except (ValueError, TypeError):
                return -1

        resultado[coluna_cluster_alinhado] = resultado[coluna_cluster_origem].map(
            _mapear
        )
        return resultado
