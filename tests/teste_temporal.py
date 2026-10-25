"""Testes automatizados para alinhamento e evolução temporal de clusters."""

import numpy as np
import pandas as pd

from app.analise_temporal.alinhador_clusters import AlinhadorClustersTemporal
from app.analise_temporal.rastreador_evolucao import RastreadorEvolucaoTemporal


def teste_alinhamento_clusters_permutados() -> None:
    """Valida a resolução ótima de permutação de clusters entre janelas temporais."""
    alinhador = AlinhadorClustersTemporal()

    # t0: cluster 0 próximo de (10, 10), cluster 1 próximo de (80, 80)
    centroides_t0 = np.array(
        [
            [10.0, 10.0],
            [80.0, 80.0],
        ],
        dtype=np.float64,
    )

    # t1: clusters permutados - cluster 0 em (81, 79) e cluster 1 em (9.5, 10.5)
    centroides_t1 = np.array(
        [
            [81.0, 79.0],
            [9.5, 10.5],
        ],
        dtype=np.float64,
    )

    mapeamento, dist_media = alinhador.calcular_alinhamento(
        centroides_t0, centroides_t1, ids_t0=[0, 1], ids_t1=[0, 1]
    )

    # O cluster 0 de t1 deve ser alinhado com o cluster 1 de t0
    # O cluster 1 de t1 deve ser alinhado com o cluster 0 de t0
    assert mapeamento[0] == 1
    assert mapeamento[1] == 0
    assert dist_media < 2.0

    df_t1 = pd.DataFrame({"cluster_id": [0, 0, 1, 1]})
    df_alinhado = alinhador.aplicar_alinhamento_dataframe(df_t1, mapeamento)
    assert list(df_alinhado["cluster_id_alinhado"]) == [1, 1, 0, 0]


def teste_rastreador_evolucao_temporal() -> None:
    """Valida o cálculo de séries temporais agregadas por janela mensal."""
    rastreador = RastreadorEvolucaoTemporal()

    df_dados = pd.DataFrame(
        {
            "timestamp_created": [
                1704067200,  # 2024-01-01
                1704153600,  # 2024-01-02
                1706745600,  # 2024-02-01
                1706832000,  # 2024-02-02
            ],
            "cluster_id": [0, 1, 0, 1],
            "voted_up": [True, False, True, True],
            "playtime_forever": [100, 50, 200, 80],
        }
    )

    evolucao = rastreador.calcular_evolucao_temporal(df_dados)
    assert not evolucao.empty
    assert "ano_mes" in evolucao.columns
    assert "proporcao_janela_percentual" in evolucao.columns
    assert "taxa_reviews_positivas" in evolucao.columns
    assert len(evolucao) == 4  # 2 clusters x 2 meses
