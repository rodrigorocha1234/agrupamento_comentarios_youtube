"""Estratégia de agrupamento baseada em densidade utilizando DBSCAN."""

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.cluster import DBSCAN

from app.agrupamento_modelos.avaliador_qualidade import (
    AvaliadorQualidade,
    MetricasAgrupamento,
)


class AgrupadorDBSCAN:
    """Implementa clusterização por densidade DBSCAN tratando rótulos -1 como ruído."""

    def __init__(
        self,
        eps: float = 0.5,
        min_samples: int = 5,
        metric: str = "cosine",
        algorithm: str = "auto",
    ) -> None:
        self._eps: float = eps
        self._min_samples: int = max(1, min_samples)
        self._metric: str = metric
        self._algorithm: str = algorithm
        self._modelo: DBSCAN | None = None

    def ajustar_e_agrupar(
        self,
        matriz: csr_matrix | np.ndarray,
    ) -> tuple[list[int], MetricasAgrupamento]:
        """Ajusta o DBSCAN e retorna os rótulos de cluster com identificação de ruído."""
        n_amostras = matriz.shape[0] if matriz.shape else 0
        if n_amostras == 0:
            return [], AvaliadorQualidade.avaliar(matriz, [])

        min_samples_efetivo = max(1, min(self._min_samples, n_amostras))
        self._modelo = DBSCAN(
            eps=self._eps,
            min_samples=min_samples_efetivo,
            metric=self._metric,
            algorithm=self._algorithm,
        )

        rotulos_arr = self._modelo.fit_predict(matriz)
        rotulos_lista = [int(r) for r in rotulos_arr]
        metricas = AvaliadorQualidade.avaliar(matriz, rotulos_arr)
        return rotulos_lista, metricas

    def obter_modelo(self) -> DBSCAN | None:
        """Retorna o modelo DBSCAN ajustado."""
        return self._modelo

