"""Estruturas imutáveis para relatório de avaliação estatística de clusters."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResultadoAvaliacao:
    """Métricas estruturadas e diagnósticos da partição de clusters."""

    total_amostras: int
    total_clusters: int
    total_ruido: int
    proporcao_ruido: float
    silhouette_global: float | None
    silhouette_sem_ruido: float | None
    davies_bouldin: float | None
    calinski_harabasz: float | None
    tamanhos_clusters: dict[int, int]
