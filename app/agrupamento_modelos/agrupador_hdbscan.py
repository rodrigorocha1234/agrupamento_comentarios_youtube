"""Estratégia de agrupamento baseada em densidade hierárquica via HDBSCAN."""

from typing import cast
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.cluster import HDBSCAN

from app.agrupamento_modelos.avaliador_qualidade import (
    AvaliadorQualidade,
    MetricasAgrupamento,
)


class AgrupadorHDBSCAN:
    """Implementa clusterização por densidade hierárquica tratando -1 como ruído."""

    def __init__(
        self,
        min_cluster_size: int = 8,
        min_samples: int = 5,
        metric: str = "euclidean",
        cluster_selection_method: str = "eom",
    ) -> None:
        self._min_cluster_size: int = max(2, min_cluster_size)
        self._min_samples: int = max(1, min_samples)
        self._metric: str = metric
        self._cluster_selection_method: str = cluster_selection_method
        self._modelo: HDBSCAN | None = None

    def ajustar_e_agrupar(
        self,
        matriz: csr_matrix | np.ndarray,
    ) -> tuple[list[int], MetricasAgrupamento]:
        """Ajusta o HDBSCAN e retorna os rótulos e métricas consolidadas."""
        n_amostras = matriz.shape[0] if matriz.shape else 0
        if n_amostras == 0:
            return [], AvaliadorQualidade.avaliar(matriz, [])

        cluster_size_efetivo = max(2, min(self._min_cluster_size, n_amostras))
        samples_efetivo = max(1, min(self._min_samples, n_amostras))

        # Se for matriz esparsa e a métrica for euclidean, converter para dense array
        if isinstance(matriz, csr_matrix):
            dados_entrada = matriz.toarray()
        else:
            dados_entrada = matriz

        self._modelo = HDBSCAN(
            min_cluster_size=cluster_size_efetivo,
            min_samples=samples_efetivo,
            metric=self._metric,
            cluster_selection_method=self._cluster_selection_method,
        )

        rotulos_arr = self._modelo.fit_predict(dados_entrada)
        rotulos_lista = [int(r) for r in rotulos_arr]
        metricas = AvaliadorQualidade.avaliar(matriz, rotulos_arr)
        return rotulos_lista, metricas

    def obter_probabilidades(self) -> np.ndarray | None:
        """Retorna as probabilidades de pertinência ao cluster de cada amostra."""
        if self._modelo is None or not hasattr(self._modelo, "probabilities_"):
            return None
        return cast(np.ndarray, self._modelo.probabilities_)
