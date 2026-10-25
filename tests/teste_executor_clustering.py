"""Testes unitários para o ExecutorClustering."""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import make_blobs

from app.clustering.executor_clustering import ExecutorClustering
from app.clustering.rastreador_mlflow import RastreadorMLflow
from app.conf_yaml import (
    ConfigAlgoritmosClustering,
    ConfigClusteringInfo,
    ConfigParametrosKMeans,
)
from app.contratos.repositorio import ProtocoloRepositorioLakehouse
from app.excecoes import ErroClustering


@pytest.fixture
def matriz_e_metadados_sinteticos() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Gera matriz numérica sintética e respectivo dataframe de metadados."""
    resultado = make_blobs(n_samples=50, centers=3, n_features=4, random_state=42)
    matriz_array = np.asarray(resultado[0], dtype=np.float64)

    df_matriz = pd.DataFrame(matriz_array, columns=[f"feat_{i}" for i in range(4)])
    df_meta = pd.DataFrame(
        {
            "recommendationid": [f"rec_{i}" for i in range(50)],
            "voted_up": [i % 2 == 0 for i in range(50)],
        }
    )
    return df_matriz, df_meta


def test_executor_clustering_sem_mlflow_sem_lakehouse(
    matriz_e_metadados_sinteticos: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    """Verifica execução básica do clustering sem serviços externos."""
    df_matriz, df_meta = matriz_e_metadados_sinteticos
    config = ConfigClusteringInfo(
        algoritmo="kmeans",
        algoritmos=ConfigAlgoritmosClustering(
            kmeans=ConfigParametrosKMeans(n_clusters=3),
        ),
    )
    executor = ExecutorClustering(config_clustering=config)

    resultado = executor.executar(df_matriz, metadados=df_meta)

    assert len(resultado.rotulos) == 50
    assert len(set(resultado.rotulos)) == 3
    assert resultado.metricas.quantidade_clusters == 3
    assert resultado.metricas.silhouette_score is not None
    assert "cluster" in resultado.dados_com_rotulos.columns
    assert resultado.dados_com_rotulos["recommendationid"].iloc[0] == "rec_0"
    assert resultado.run_id is None
    assert resultado.uri_gold_clusters == ""


def test_executor_clustering_com_rastreador_mlflow_mock(
    matriz_e_metadados_sinteticos: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    """Verifica que o ExecutorClustering envia parâmetros, métricas e modelo ao MLflow."""
    df_matriz, _ = matriz_e_metadados_sinteticos
    config_clust = ConfigClusteringInfo(
        algoritmo="kmeans",
        algoritmos=ConfigAlgoritmosClustering(
            kmeans=ConfigParametrosKMeans(n_clusters=3),
        ),
    )
    rastreador_mock = MagicMock(spec=RastreadorMLflow)
    rastreador_mock.iniciar_execucao.return_value.__enter__.return_value = MagicMock(
        info=MagicMock(run_id="run-teste-123")
    )

    executor = ExecutorClustering(
        config_clustering=config_clust,
        rastreador=rastreador_mock,
    )
    resultado = executor.executar(df_matriz)

    assert resultado.run_id == "run-teste-123"
    rastreador_mock.registrar_parametros.assert_called_once()
    rastreador_mock.registrar_metricas.assert_called_once()
    rastreador_mock.registrar_modelo_sklearn.assert_called_once()


def test_executor_clustering_com_repositorio_lakehouse(
    matriz_e_metadados_sinteticos: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    """Verifica que a visão Gold 'clusters' é persistida quando repositório e identificador são passados."""
    df_matriz, df_meta = matriz_e_metadados_sinteticos
    config_clust = ConfigClusteringInfo(
        algoritmo="kmeans",
        algoritmos=ConfigAlgoritmosClustering(
            kmeans=ConfigParametrosKMeans(n_clusters=3),
        ),
    )
    repo_mock = MagicMock(spec=ProtocoloRepositorioLakehouse)
    repo_mock.gravar_gold.return_value = "s3://steam-reviews/gold/730/20261025_clusters.parquet"

    executor = ExecutorClustering(config_clustering=config_clust)
    resultado = executor.executar(
        df_matriz,
        metadados=df_meta,
        identificador=730,
        repositorio=repo_mock,
    )

    assert resultado.uri_gold_clusters == "s3://steam-reviews/gold/730/20261025_clusters.parquet"
    repo_mock.gravar_gold.assert_called_once()
    _, kwargs = repo_mock.gravar_gold.call_args
    assert kwargs["identificador"] == 730
    assert kwargs["sufixo_visao"] == "clusters"


def test_executor_clustering_matriz_invalida() -> None:
    """Verifica que o ExecutorClustering rejeita matrizes vazias ou unidimensionais."""
    config_clust = ConfigClusteringInfo(
        algoritmo="kmeans",
        algoritmos=ConfigAlgoritmosClustering(
            kmeans=ConfigParametrosKMeans(n_clusters=2),
        ),
    )
    executor = ExecutorClustering(config_clustering=config_clust)

    with pytest.raises(ErroClustering, match="Matriz de treino inválida"):
        executor.executar(np.array([]))

    with pytest.raises(ErroClustering, match="Matriz de treino inválida"):
        executor.executar(np.array([1.0, 2.0, 3.0]))
