"""Testes unitários e de integração para rastreamento e serving no MLflow."""

from unittest.mock import MagicMock
import pytest
import requests

from app.agrupamento_modelos.avaliador_qualidade import MetricasAgrupamento
from app.integracao_mlflow.adaptador_serving import (
    AdaptadorServing,
    AdaptadorServingErro,
)
from app.integracao_mlflow.rastreador_experimentos import (
    RastreadorExperimentos,
)


def test_rastreador_experimentos_integracao_mlflow() -> None:
    """Valida registro real de run, métricas e parâmetros no MLflow Server ativo (127.0.0.1:5000)."""
    rastreador = RastreadorExperimentos(tracking_uri="http://127.0.0.1:5000")
    metricas = MetricasAgrupamento(
        quantidade_clusters=3,
        fracao_ruido=0.05,
        pontuacao_silhueta=0.55,
        indice_davies_bouldin=0.82,
        pontuacao_calinski_harabasz=145.2,
    )
    parametros: dict[str, object] = {
        "n_clusters": 3,
        "random_state": 42,
    }

    from typing import cast
    from sklearn.cluster import KMeans
    modelo_km = KMeans(n_clusters=3, random_state=42, n_init=cast(str, 10)).fit([[0.0, 1.0], [1.0, 0.0], [5.0, 5.0]])

    run_id = rastreador.registrar_execucao(
        nome_experimento="teste_experimento_unitario",
        tecnica="kmeans",
        parametros=parametros,
        metricas=metricas,
        uri_manifesto_s3="s3://youtube-comentarios/bronze/manifesto.json",
        modelo_sklearn=modelo_km,
        nome_modelo_registry="modelo_kmeans_teste",
    )

    assert isinstance(run_id, str)
    assert len(run_id) > 10


def test_adaptador_serving_invocacao_sucesso() -> None:
    """Testa consumo do endpoint /invocations retornando predições de clusters."""
    sessao_mock = MagicMock(spec=requests.Session)
    resposta_mock = requests.Response()
    resposta_mock.status_code = 200
    resposta_mock.json = MagicMock(return_value={"predictions": [1, 2, -1]})
    sessao_mock.post.return_value = resposta_mock

    adaptador = AdaptadorServing(
        serving_url="http://127.0.0.1:8080",
        sessao_http=sessao_mock,
    )
    predicoes = adaptador.invocar_predicao(["Texto 1", "Texto 2", "Texto 3"])

    assert predicoes == [1, 2, -1]
    sessao_mock.post.assert_called_once()


def test_adaptador_serving_erro_conexao_lanca_excecao() -> None:
    """Garante lançamento de AdaptadorServingErro quando o servidor falha."""
    sessao_mock = MagicMock(spec=requests.Session)
    sessao_mock.post.side_effect = requests.RequestException("Conexao recusada")

    adaptador = AdaptadorServing(
        serving_url="http://127.0.0.1:8080",
        sessao_http=sessao_mock,
    )
    with pytest.raises(AdaptadorServingErro):
        adaptador.invocar_predicao(["Texto teste"])
