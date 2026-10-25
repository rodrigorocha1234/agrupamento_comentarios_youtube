"""Testes unitários e de integração para a API FastAPI."""

from unittest.mock import MagicMock

import numpy as np
from fastapi.testclient import TestClient

from app.analise_clusters.analisador_clusters import (
    PerfilCluster,
    ResumoAnaliseClusters,
)
from app.clustering.motores_sklearn import MotorDBSCAN, MotorKMeans
from app.conf_yaml import (
    ConfigAPIInfo,
    ConfigClusteringInfo,
    ConfigLimitesAPI,
    ConfigParametrosDBSCAN,
    ConfigParametrosKMeans,
)
from app.contratos.repositorio import ProtocoloRepositorioLakehouse
from app.servico_api.aplicacao import criar_aplicacao_fastapi
from app.servico_api.estado_aplicacao import EstadoAplicacao


def test_api_health() -> None:
    """Verifica rota /health."""
    app = criar_aplicacao_fastapi()
    cliente = TestClient(app)

    resposta = cliente.get("/health")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["status"] == "ok"
    assert "servicos" in dados


def test_api_ready_status_incompleto_e_completo() -> None:
    """Verifica rota /ready tanto no estado não pronto (503) quanto pronto (200)."""
    estado_vazio = EstadoAplicacao()
    app_vazio = criar_aplicacao_fastapi(estado_vazio)
    cliente_vazio = TestClient(app_vazio)

    resp_vazio = cliente_vazio.get("/ready")
    assert resp_vazio.status_code == 503
    assert resp_vazio.json()["pronto"] is False

    # Estado pronto
    repo_mock = MagicMock(spec=ProtocoloRepositorioLakehouse)
    motor_mock = MagicMock(spec=MotorKMeans)
    estado_pronto = EstadoAplicacao(
        motor=motor_mock,
        repositorio=repo_mock,
    )
    app_pronto = criar_aplicacao_fastapi(estado_pronto)
    cliente_pronto = TestClient(app_pronto)

    resp_pronto = cliente_pronto.get("/ready")
    assert resp_pronto.status_code == 200
    assert resp_pronto.json()["pronto"] is True


def test_api_metrics_prometheus() -> None:
    """Verifica rota /metrics no formato padrão Prometheus."""
    app = criar_aplicacao_fastapi()
    cliente = TestClient(app)

    resposta = cliente.get("/metrics")
    assert resposta.status_code == 200
    assert "clustering_api_requisicoes_total" in resposta.text


def test_api_info_modelo_e_clusters() -> None:
    """Verifica endpoints /api/v1/model e /api/v1/clusters."""
    resumo = ResumoAnaliseClusters(
        perfis=[
            PerfilCluster(
                id_cluster=0,
                nome_rotulo="Cluster 0",
                quantidade_amostras=10,
                proporcao_amostras=1.0,
                medias_atributos={"attr_1": 5.0},
                medianas_atributos={"attr_1": 5.0},
            )
        ],
        total_amostras=10,
        quantidade_clusters_validos=1,
        quantidade_ruido=0,
        proporcao_ruido=0.0,
        atributos_analisados=["attr_1"],
    )

    estado = EstadoAplicacao(
        resumo_clusters=resumo,
        nomes_atributos=["attr_1"],
    )
    app = criar_aplicacao_fastapi(estado)
    cliente = TestClient(app)

    resp_model = cliente.get("/api/v1/model")
    assert resp_model.status_code == 200
    assert resp_model.json()["nomes_atributos_esperados"] == ["attr_1"]

    resp_clusters = cliente.get("/api/v1/clusters")
    assert resp_clusters.status_code == 200
    assert resp_clusters.json()["total_amostras"] == 10

    resp_cluster_0 = cliente.get("/api/v1/clusters/0")
    assert resp_cluster_0.status_code == 200
    assert resp_cluster_0.json()["id_cluster"] == 0

    resp_inexistente = cliente.get("/api/v1/clusters/999")
    assert resp_inexistente.status_code == 404


def test_api_predict_com_kmeans_sucesso() -> None:
    """Verifica inferência bem sucedida com algoritmo que suporta predição (KMeans)."""
    motor = MotorKMeans(
        parametros=ConfigParametrosKMeans(n_clusters=2),
        random_state=42,
    )
    # Treina com dados sintéticos
    dados = np.array([[1.0, 1.0], [1.1, 1.2], [10.0, 10.0], [10.2, 9.8]], dtype=np.float64)
    motor.ajustar(dados)

    estado = EstadoAplicacao(
        config_clustering=ConfigClusteringInfo(algoritmo="kmeans"),
        motor=motor,
        nomes_atributos=["feat_1", "feat_2"],
    )
    app = criar_aplicacao_fastapi(estado)
    cliente = TestClient(app)

    # Predição de ponto único
    payload = {"atributos": {"feat_1": 1.05, "feat_2": 1.1}}
    resposta = cliente.post("/api/v1/predict", json=payload)
    assert resposta.status_code == 200
    conteudo = resposta.json()
    assert conteudo["cluster_atribuido"] in [0, 1]
    assert conteudo["distancia_centroide"] is not None

    # Predição em lote
    payload_lote = {
        "amostras": [
            {"feat_1": 1.0, "feat_2": 1.0},
            {"feat_1": 10.0, "feat_2": 10.0},
        ]
    }
    resp_lote = cliente.post("/api/v1/predict-batch", json=payload_lote)
    assert resp_lote.status_code == 200
    assert len(resp_lote.json()["clusters_atribuidos"]) == 2


def test_api_predict_bloqueada_para_dbscan_sem_suporte() -> None:
    """Garante que a API rejeita previsão com HTTP 422 para algoritmos que não suportam inferência."""
    motor = MotorDBSCAN(parametros=ConfigParametrosDBSCAN(eps=0.5, min_samples=2))
    dados = np.array([[1.0, 1.0], [1.1, 1.2], [5.0, 5.0]], dtype=np.float64)
    motor.ajustar(dados)

    estado = EstadoAplicacao(
        config_clustering=ConfigClusteringInfo(algoritmo="dbscan"),
        motor=motor,
        nomes_atributos=["feat_1", "feat_2"],
    )
    app = criar_aplicacao_fastapi(estado)
    cliente = TestClient(app)

    payload = {"atributos": {"feat_1": 1.0, "feat_2": 1.0}}
    resposta = cliente.post("/api/v1/predict", json=payload)

    assert resposta.status_code == 422
    assert "não suporta previsão" in resposta.json()["detail"]


def test_api_predict_batch_validacao_limites() -> None:
    """Verifica rejeição quando o lote for vazio ou ultrapassar o limite configurado."""
    motor = MotorKMeans(parametros=ConfigParametrosKMeans(n_clusters=2))
    motor.ajustar(np.array([[1.0], [2.0]], dtype=np.float64))

    config_api = ConfigAPIInfo(limites=ConfigLimitesAPI(tamanho_lote_maximo=2))
    estado = EstadoAplicacao(
        config_api=config_api,
        motor=motor,
        nomes_atributos=["feat_1"],
    )
    app = criar_aplicacao_fastapi(estado)
    cliente = TestClient(app)

    # Lote vazio -> 400
    resp_vazio = cliente.post("/api/v1/predict-batch", json={"amostras": []})
    assert resp_vazio.status_code == 400

    # Lote maior que limite (3 > 2) -> 400
    amostras_grandes = [{"feat_1": 1.0}, {"feat_1": 2.0}, {"feat_1": 3.0}]
    resp_grande = cliente.post("/api/v1/predict-batch", json={"amostras": amostras_grandes})
    assert resp_grande.status_code == 400
    assert "excede o limite" in resp_grande.json()["detail"]
