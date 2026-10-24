"""Avaliador estatístico de qualidade de partições de clustering."""

from collections import Counter
from typing import final

import numpy as np
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

from app.avaliacao_modelos.metricas_estatisticas import ResultadoAvaliacao


@final
class AvaliadorClusters:
    """Calcula Silhouette, Davies-Bouldin, Calinski-Harabasz e diagnósticos de ruído."""

    def avaliar(self, matriz_x: np.ndarray, rotulos: np.ndarray) -> ResultadoAvaliacao:
        """Avalia a qualidade estatística do agrupamento de forma transparente."""
        total_amostras = len(rotulos)
        if total_amostras == 0:
            return ResultadoAvaliacao(
                total_amostras=0,
                total_clusters=0,
                total_ruido=0,
                proporcao_ruido=0.0,
                silhouette_global=None,
                silhouette_sem_ruido=None,
                davies_bouldin=None,
                calinski_harabasz=None,
                tamanhos_clusters={},
            )

        contagem = Counter(int(r) for r in rotulos)
        rotulos_unicos = set(contagem.keys())
        rotulos_validos = {r for r in rotulos_unicos if r != -1}
        total_ruido = contagem.get(-1, 0)
        proporcao_ruido = float(total_ruido / total_amostras)

        silhouette_global: float | None = None
        silhouette_sem_ruido: float | None = None
        davies_bouldin: float | None = None
        calinski_harabasz: float | None = None

        # Silhouette global (se houver pelo menos 2 partições no total)
        if len(rotulos_unicos) >= 2 and len(rotulos_unicos) < total_amostras:
            try:
                silhouette_global = float(silhouette_score(matriz_x, rotulos))
            except ValueError:
                silhouette_global = None

        # Métricas apenas em pontos não ruído
        if len(rotulos_validos) >= 2:
            mascara_sem_ruido = rotulos != -1
            x_valido = matriz_x[mascara_sem_ruido]
            rotulos_validos_arr = rotulos[mascara_sem_ruido]

            if len(rotulos_validos_arr) > len(rotulos_validos):
                try:
                    silhouette_sem_ruido = float(
                        silhouette_score(x_valido, rotulos_validos_arr)
                    )
                except ValueError:
                    silhouette_sem_ruido = None

                try:
                    davies_bouldin = float(
                        davies_bouldin_score(x_valido, rotulos_validos_arr)
                    )
                except ValueError:
                    davies_bouldin = None

                try:
                    calinski_harabasz = float(
                        calinski_harabasz_score(x_valido, rotulos_validos_arr)
                    )
                except ValueError:
                    calinski_harabasz = None

        return ResultadoAvaliacao(
            total_amostras=total_amostras,
            total_clusters=len(rotulos_validos),
            total_ruido=total_ruido,
            proporcao_ruido=proporcao_ruido,
            silhouette_global=silhouette_global,
            silhouette_sem_ruido=silhouette_sem_ruido,
            davies_bouldin=davies_bouldin,
            calinski_harabasz=calinski_harabasz,
            tamanhos_clusters=dict(contagem),
        )
