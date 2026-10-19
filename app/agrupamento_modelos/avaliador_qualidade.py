"""Avaliação estatística e métricas de qualidade de agrupamentos de dados."""

from dataclasses import dataclass
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)


@dataclass(frozen=True, slots=True)
class MetricasAgrupamento:
    """Métricas consolidadas de avaliação do cluster."""

    quantidade_clusters: int
    fracao_ruido: float
    pontuacao_silhueta: float | None
    indice_davies_bouldin: float | None
    pontuacao_calinski_harabasz: float | None


class AvaliadorQualidade:
    """Calcula métricas de coesão, separação e ruído sem assumir distribuições homogêneas."""

    @classmethod
    def avaliar(
        cls,
        matriz: csr_matrix | np.ndarray,
        rotulos: list[int] | np.ndarray,
    ) -> MetricasAgrupamento:
        """Calcula as métricas para os rótulos gerados, isolando o ruído (-1)."""
        rotulos_arr = np.asarray(rotulos)
        total_amostras = len(rotulos_arr)

        if total_amostras == 0:
            return MetricasAgrupamento(
                quantidade_clusters=0,
                fracao_ruido=0.0,
                pontuacao_silhueta=None,
                indice_davies_bouldin=None,
                pontuacao_calinski_harabasz=None,
            )

        rotulos_unicos = set(rotulos_arr)
        rotulos_validos = {r for r in rotulos_unicos if r != -1}
        qtd_clusters = len(rotulos_validos)

        amostras_ruido = int(np.sum(rotulos_arr == -1))
        fracao_ruido = float(amostras_ruido / total_amostras)

        # Para cálculo de distâncias internas, removemos os pontos de ruído (-1)
        mascara_validos = rotulos_arr != -1
        qtd_validos = int(np.sum(mascara_validos))

        silhueta: float | None = None
        davies_bouldin: float | None = None
        calinski: float | None = None

        if qtd_clusters > 1 and qtd_validos > qtd_clusters:
            dados_validos = matriz[mascara_validos]
            if isinstance(dados_validos, csr_matrix):
                dados_avaliar = dados_validos.toarray()
            else:
                dados_avaliar = dados_validos
            rotulos_filtrados = rotulos_arr[mascara_validos]

            try:
                silhueta = float(silhouette_score(dados_avaliar, rotulos_filtrados))
            except Exception:
                silhueta = None

            try:
                davies_bouldin = float(davies_bouldin_score(dados_avaliar, rotulos_filtrados))
            except Exception:
                davies_bouldin = None

            try:
                calinski = float(calinski_harabasz_score(dados_avaliar, rotulos_filtrados))
            except Exception:
                calinski = None

        return MetricasAgrupamento(
            quantidade_clusters=qtd_clusters,
            fracao_ruido=fracao_ruido,
            pontuacao_silhueta=silhueta,
            indice_davies_bouldin=davies_bouldin,
            pontuacao_calinski_harabasz=calinski,
        )
