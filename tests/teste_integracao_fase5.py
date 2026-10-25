"""Testes integrados de ponta a ponta da Fase 5: PostgreSQL, Temporal, FastAPI e AutoML."""

import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs
from starlette.testclient import TestClient

from app.agrupamento_modelos.selecionador_automl import SelecionadorModelosAutoML
from app.analise_temporal.alinhador_clusters import AlinhadorClustersTemporal
from app.analise_temporal.rastreador_evolucao import RastreadorEvolucaoTemporal
from app.persistencia_staging.fabrica_staging import FabricaStaging
from app.persistencia_staging.repositorio_postgres import RepositorioStagingPostgres
from app.persistencia_staging.unidade_postgres import UnidadeTrabalhoPostgres
from app.servico_api.aplicacao_fastapi import criar_aplicacao


def teste_integracao_fase5_completa() -> None:
    """Valida a integração dos quatro pilares da Fase 5 em um único ciclo analítico."""
    # 1. Fábrica de Staging resolvendo PostgreSQL
    fabrica = FabricaStaging()
    uow, repo = fabrica.criar_staging("postgres")
    assert isinstance(uow, UnidadeTrabalhoPostgres)
    assert isinstance(repo, RepositorioStagingPostgres)

    # 2. Análise Temporal e Estabilidade de Clusters
    alinhador = AlinhadorClustersTemporal()
    c_t0 = np.array([[5.0, 5.0], [50.0, 50.0]], dtype=np.float64)
    c_t1 = np.array([[49.5, 50.2], [4.9, 5.1]], dtype=np.float64)  # Permutados
    mapa_alinhado, dist = alinhador.calcular_alinhamento(c_t0, c_t1)
    assert mapa_alinhado[0] == 1
    assert mapa_alinhado[1] == 0
    assert dist < 1.0

    # Rastreamento de evolução temporal
    rastreador = RastreadorEvolucaoTemporal()
    df_temporal = pd.DataFrame(
        {
            "timestamp_created": [1704067200, 1704153600, 1706745600],
            "cluster_id": [0, 1, 0],
            "voted_up": [True, False, True],
            "playtime_forever": [1000, 500, 1200],
        }
    )
    df_resumo_temporal = rastreador.calcular_evolucao_temporal(df_temporal)
    assert not df_resumo_temporal.empty
    assert "proporcao_janela_percentual" in df_resumo_temporal.columns

    # 3. AutoML e Eleição de Modelo
    retorno_blobs = make_blobs(n_samples=100, centers=2, n_features=2, random_state=42)
    matriz_x = np.asarray(retorno_blobs[0], dtype=np.float64)

    selecionador = SelecionadorModelosAutoML()
    modelo, avaliacao, algoritmo, score = selecionador.selecionar_melhor_modelo(
        matriz_x,
        candidatos=[
            ("kmeans", {"n_clusters": 2, "n_init": 10}),
            ("kmeans", {"n_clusters": 4, "n_init": 10}),
        ],
    )
    assert modelo is not None
    assert algoritmo == "kmeans"
    assert avaliacao.total_clusters == 2
    assert score > 0.0

    # 4. Serviço de API REST FastAPI
    app = criar_aplicacao()
    cliente = TestClient(app)

    # Verificação de rotas
    resp_health = cliente.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "healthy"

    resp_metrics = cliente.get("/metrics")
    assert resp_metrics.status_code == 200

    resp_clusters = cliente.get("/api/v1/jogos/427520/clusters")
    assert resp_clusters.status_code == 200
    assert resp_clusters.json()["appid"] == 427520

    resp_reviews = cliente.get("/api/v1/jogos/427520/reviews?limite=10")
    assert resp_reviews.status_code == 200
    assert resp_reviews.json()["total_retornado"] > 0

    resp_pred = cliente.post(
        "/api/v1/jogos/427520/predizer",
        json={"dados_atributos": [[10.0, 50.0], [50.0, 10.0]]},
    )
    assert resp_pred.status_code == 200
    assert len(resp_pred.json()["clusters_atribuidos"]) == 2
