"""Avaliador de métricas de clustering com isolamento de ruído e tratamento de casos de borda."""

from collections import Counter
from dataclasses import dataclass

import numpy as np
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)


@dataclass(frozen=True)
class MetricasClustering:
    """Conjunto de métricas escalares calculadas para a solução de agrupamento."""

    quantidade_clusters: int
    quantidade_pontos_ruido: int
    proporcao_ruido: float
    silhouette_score: float | None
    davies_bouldin_index: float | None
    calinski_harabasz_score: float | None
    tamanhos_clusters: dict[int, int]

    def para_dicionario(self) -> dict[str, float]:
        """Converte as métricas numéricas disponíveis para registro em plataformas de telemetria."""
        resultado: dict[str, float] = {
            "quantidade_clusters": float(self.quantidade_clusters),
            "quantidade_pontos_ruido": float(self.quantidade_pontos_ruido),
            "proporcao_ruido": self.proporcao_ruido,
        }
        if self.silhouette_score is not None:
            resultado["silhouette_score"] = self.silhouette_score
        if self.davies_bouldin_index is not None:
            resultado["davies_bouldin_index"] = self.davies_bouldin_index
        if self.calinski_harabasz_score is not None:
            resultado["calinski_harabasz_score"] = self.calinski_harabasz_score
        return resultado


class AvaliadorClusters:
    """Calcula métricas de qualidade e separação de clusters de forma adaptativa."""

    @staticmethod
    def avaliar(matriz: np.ndarray, rotulos: list[int]) -> MetricasClustering:
        """Avalia a qualidade dos clusters considerando presença de ruído (-1).

        Args:
            matriz: Matriz de atributos de treino de dimensão (n_amostras, n_features).
            rotulos: Lista de inteiros contendo os clusters atribuídos a cada ponto.

        Retorna:
            Instância de MetricasClustering contendo índices e contagens calculados.
        """
        total_amostras = len(rotulos)
        if total_amostras == 0:
            return MetricasClustering(
                quantidade_clusters=0,
                quantidade_pontos_ruido=0,
                proporcao_ruido=0.0,
                silhouette_score=None,
                davies_bouldin_index=None,
                calinski_harabasz_score=None,
                tamanhos_clusters={},
            )

        contagem = Counter(rotulos)
        qtd_ruido = contagem.get(-1, 0)
        proporcao_ruido = qtd_ruido / total_amostras

        # Clusters válidos são estritamente os não-ruído (>= 0)
        clusters_validos = sorted([c for c in contagem if c >= 0])
        qtd_clusters = len(clusters_validos)
        tamanhos = {c: contagem[c] for c in clusters_validos}
        if qtd_ruido > 0:
            tamanhos[-1] = qtd_ruido

        # Caso de borda 1: Sem clusters válidos (100% ruído) ou menos de 2 clusters
        # Silhouette e demais índices exigem pelo menos 2 clusters e mais amostras que clusters
        if qtd_clusters < 2:
            return MetricasClustering(
                quantidade_clusters=qtd_clusters,
                quantidade_pontos_ruido=qtd_ruido,
                proporcao_ruido=proporcao_ruido,
                silhouette_score=None,
                davies_bouldin_index=None,
                calinski_harabasz_score=None,
                tamanhos_clusters=tamanhos,
            )

        # Filtra pontos de ruído para avaliar apenas os agrupamentos reais
        mascara_validos = np.asarray(rotulos) >= 0
        matriz_filtrada = matriz[mascara_validos]
        rotulos_filtrados = np.asarray(rotulos)[mascara_validos]

        # Caso de borda 2: Menos amostras filtradas do que 2
        if len(rotulos_filtrados) < 2 or len(np.unique(rotulos_filtrados)) < 2:
            return MetricasClustering(
                quantidade_clusters=qtd_clusters,
                quantidade_pontos_ruido=qtd_ruido,
                proporcao_ruido=proporcao_ruido,
                silhouette_score=None,
                davies_bouldin_index=None,
                calinski_harabasz_score=None,
                tamanhos_clusters=tamanhos,
            )

        # Cálculo seguro dos índices
        try:
            sil = float(silhouette_score(matriz_filtrada, rotulos_filtrados))
        except (ValueError, ZeroDivisionError):
            sil = None

        try:
            db = float(davies_bouldin_score(matriz_filtrada, rotulos_filtrados))
        except (ValueError, ZeroDivisionError):
            db = None

        try:
            ch = float(calinski_harabasz_score(matriz_filtrada, rotulos_filtrados))
        except (ValueError, ZeroDivisionError):
            ch = None

        return MetricasClustering(
            quantidade_clusters=qtd_clusters,
            quantidade_pontos_ruido=qtd_ruido,
            proporcao_ruido=proporcao_ruido,
            silhouette_score=sil,
            davies_bouldin_index=db,
            calinski_harabasz_score=ch,
            tamanhos_clusters=tamanhos,
        )
