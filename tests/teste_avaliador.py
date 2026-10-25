"""Testes unitários para o AvaliadorClusters e RastreadorMLflow."""

from unittest.mock import MagicMock, patch

import numpy as np
from sklearn.datasets import make_blobs

from app.clustering.avaliador_clusters import AvaliadorClusters
from app.clustering.rastreador_mlflow import RastreadorMLflow
from app.conf_yaml import ConfigMLflowInfo


def test_avaliador_clusters_dados_bem_separados() -> None:
    """Verifica que o AvaliadorClusters calcula métricas válidas em agrupamentos claros."""
    resultado_blobs = make_blobs(n_samples=100, centers=3, n_features=4, random_state=42)
    X: np.ndarray = np.asarray(resultado_blobs[0], dtype=np.float64)
    y = np.asarray(resultado_blobs[1], dtype=np.int64)
    rotulos = [int(val) for val in y]

    metricas = AvaliadorClusters.avaliar(X, rotulos)

    assert metricas.quantidade_clusters == 3
    assert metricas.quantidade_pontos_ruido == 0
    assert metricas.proporcao_ruido == 0.0
    assert metricas.silhouette_score is not None
    assert metricas.silhouette_score > 0.5
    assert metricas.davies_bouldin_index is not None
    assert metricas.calinski_harabasz_score is not None
    assert len(metricas.tamanhos_clusters) == 3

    dicionario = metricas.para_dicionario()
    assert "silhouette_score" in dicionario
    assert "davies_bouldin_index" in dicionario
    assert "calinski_harabasz_score" in dicionario


def test_avaliador_clusters_com_ruido() -> None:
    """Garante que amostras de ruído (-1) são isoladas para não distorcer Silhouette."""
    X = np.array(
        [
            [1.0, 1.0],
            [1.1, 1.0],
            [10.0, 10.0],
            [10.1, 10.0],
            [100.0, 100.0],  # Ponto de ruído isolado
        ]
    )
    rotulos = [0, 0, 1, 1, -1]

    metricas = AvaliadorClusters.avaliar(X, rotulos)

    assert metricas.quantidade_clusters == 2
    assert metricas.quantidade_pontos_ruido == 1
    assert np.isclose(metricas.proporcao_ruido, 0.2)
    assert -1 in metricas.tamanhos_clusters
    assert metricas.silhouette_score is not None


def test_avaliador_clusters_caso_borda_100_porcento_ruido() -> None:
    """Garante tratamento gracioso quando todas as amostras são classificadas como ruído."""
    X = np.random.randn(20, 2)
    rotulos = [-1] * 20

    metricas = AvaliadorClusters.avaliar(X, rotulos)

    assert metricas.quantidade_clusters == 0
    assert metricas.quantidade_pontos_ruido == 20
    assert metricas.proporcao_ruido == 1.0
    assert metricas.silhouette_score is None
    assert metricas.davies_bouldin_index is None
    assert metricas.calinski_harabasz_score is None


def test_avaliador_clusters_caso_borda_cluster_unico() -> None:
    """Garante que agrupamento com apenas 1 cluster não dispara erro matemático de Silhouette."""
    X = np.random.randn(20, 2)
    rotulos = [0] * 20

    metricas = AvaliadorClusters.avaliar(X, rotulos)

    assert metricas.quantidade_clusters == 1
    assert metricas.quantidade_pontos_ruido == 0
    assert metricas.proporcao_ruido == 0.0
    assert metricas.silhouette_score is None
    assert metricas.davies_bouldin_index is None
    assert metricas.calinski_harabasz_score is None


def test_avaliador_clusters_matriz_vazia() -> None:
    """Verifica comportamento com entradas vazias."""
    X = np.empty((0, 2))
    rotulos: list[int] = []

    metricas = AvaliadorClusters.avaliar(X, rotulos)
    assert metricas.quantidade_clusters == 0
    assert metricas.proporcao_ruido == 0.0


def test_rastreador_mlflow_desabilitado() -> None:
    """Verifica que quando desabilitado, o RastreadorMLflow opera em no-op seguro."""
    config = ConfigMLflowInfo(habilitado=False)
    rastreador = RastreadorMLflow(config=config)

    with rastreador.iniciar_execucao(nome_execucao="teste_desabilitado") as run:
        assert run is None

    # Chamadas de registro não devem levantar erro
    rastreador.registrar_parametros({"param1": "valor"})
    rastreador.registrar_metricas({"metrica1": 1.0})
    rastreador.registrar_tags({"tag1": "teste"})
    rastreador.registrar_artefato("caminho_inexistente.txt")


def test_rastreador_mlflow_habilitado_com_mocks() -> None:
    """Verifica chamadas da API MLflow quando o tracking está habilitado."""
    config = ConfigMLflowInfo(
        habilitado=True,
        tracking_uri="http://fake-mlflow:5000",
        experiment_name="teste_exp",
    )

    with (
        patch("mlflow.set_tracking_uri") as mock_uri,
        patch("mlflow.set_experiment") as mock_exp,
        patch("mlflow.start_run") as mock_run,
        patch("mlflow.log_params") as mock_params,
        patch("mlflow.log_metrics") as mock_metrics,
        patch("mlflow.set_tags") as mock_tags,
    ):
        mock_run.return_value.__enter__.return_value = MagicMock()
        mock_run.return_value.__exit__.return_value = None

        rastreador = RastreadorMLflow(config=config)
        mock_uri.assert_called_once_with("http://fake-mlflow:5000")
        mock_exp.assert_called_once_with("teste_exp")

        with rastreador.iniciar_execucao(nome_execucao="exec_1"):
            pass
        assert mock_run.called

        rastreador.registrar_parametros({"n_clusters": 3})
        mock_params.assert_called_once_with({"n_clusters": "3"})

        rastreador.registrar_metricas({"silhouette": 0.75})
        mock_metrics.assert_called_once_with({"silhouette": 0.75})

        rastreador.registrar_tags({"tipo": "teste"})
        mock_tags.assert_called_once_with({"tipo": "teste"})
