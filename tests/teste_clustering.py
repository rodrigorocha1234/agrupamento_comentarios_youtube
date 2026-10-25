"""Testes unitários para os motores de clustering e FabricaClustering."""

import numpy as np
import pytest
from sklearn.datasets import make_blobs

from app.clustering.fabrica_clustering import FabricaClustering
from app.clustering.motores_sklearn import MotorDBSCAN, MotorHDBSCAN, MotorKMeans
from app.conf_yaml import (
    ConfigClusteringInfo,
    ConfigParametrosDBSCAN,
    ConfigParametrosHDBSCAN,
    ConfigParametrosKMeans,
)
from app.excecoes import ErroAlgoritmoNaoSuportado, ErroClustering, ErroConfiguracao


@pytest.fixture
def dados_sinteticos_3_clusters() -> np.ndarray:
    """Gera matriz com 3 blobs bem delimitados para teste determinístico."""
    resultado_blobs = make_blobs(n_samples=60, centers=3, n_features=4, random_state=42)
    matriz: np.ndarray = np.asarray(resultado_blobs[0], dtype=np.float64)
    return matriz


def test_motor_kmeans_ajuste_centroides_e_previsao(dados_sinteticos_3_clusters: np.ndarray) -> None:
    """Verifica funcionamento completo do KMeans (ajuste, centroides e predict)."""
    params = ConfigParametrosKMeans(n_clusters=3, max_iter=100)
    motor = MotorKMeans(parametros=params, random_state=42)

    motor.ajustar(dados_sinteticos_3_clusters)
    rotulos = motor.obter_rotulos()

    assert len(rotulos) == 60
    assert len(set(rotulos)) == 3
    assert motor.tem_centroides is True

    centroides = motor.obter_centroides()
    assert centroides is not None
    assert centroides.shape == (3, 4)

    assert motor.suporta_previsao is True
    novas_amostras = np.zeros((2, 4))
    predicoes = motor.prever(novas_amostras)
    assert len(predicoes) == 2
    assert all(isinstance(p, int) for p in predicoes)


def test_motor_kmeans_falha_com_poucas_amostras() -> None:
    """Verifica lançamento de ErroClustering se n_amostras < n_clusters."""
    params = ConfigParametrosKMeans(n_clusters=5)
    motor = MotorKMeans(parametros=params)
    poucas_amostras = np.zeros((3, 2))

    with pytest.raises(ErroClustering, match="Número de amostras .* é menor do que n_clusters"):
        motor.ajustar(poucas_amostras)


def test_motor_dbscan_ajuste_ruido_e_bloqueio_previsao(dados_sinteticos_3_clusters: np.ndarray) -> None:
    """Verifica DBSCAN identificando grupos/ruído e bloqueando inferência out-of-sample."""
    params = ConfigParametrosDBSCAN(eps=1.5, min_samples=3)
    motor = MotorDBSCAN(parametros=params)

    motor.ajustar(dados_sinteticos_3_clusters)
    rotulos = motor.obter_rotulos()

    assert len(rotulos) == 60
    assert motor.tem_centroides is False
    assert motor.obter_centroides() is None

    assert motor.suporta_previsao is False
    with pytest.raises(ErroAlgoritmoNaoSuportado, match="DBSCAN é estritamente transdutivo"):
        motor.prever(np.zeros((2, 4)))


def test_motor_hdbscan_ajuste_nativo_sklearn(dados_sinteticos_3_clusters: np.ndarray) -> None:
    """Verifica HDBSCAN nativo do scikit-learn ajustando clusters e bloqueando prever()."""
    params = ConfigParametrosHDBSCAN(min_cluster_size=5)
    motor = MotorHDBSCAN(parametros=params)

    motor.ajustar(dados_sinteticos_3_clusters)
    rotulos = motor.obter_rotulos()

    assert len(rotulos) == 60
    assert motor.tem_centroides is False
    assert motor.obter_centroides() is None
    assert motor.suporta_previsao is False

    with pytest.raises(ErroAlgoritmoNaoSuportado, match="HDBSCAN opera por densidade hierárquica"):
        motor.prever(np.zeros((2, 4)))


def test_fabrica_clustering_instanciacao() -> None:
    """Verifica resolução dinâmica de KMeans, DBSCAN e HDBSCAN via FabricaClustering."""
    # 1. KMeans
    conf_kmeans = ConfigClusteringInfo(algoritmo="kmeans")
    motor_kmeans = FabricaClustering.criar_motor(conf_kmeans)
    assert isinstance(motor_kmeans, MotorKMeans)

    # 2. DBSCAN
    conf_dbscan = ConfigClusteringInfo(algoritmo="dbscan")
    motor_dbscan = FabricaClustering.criar_motor(conf_dbscan)
    assert isinstance(motor_dbscan, MotorDBSCAN)

    # 3. HDBSCAN
    conf_hdbscan = ConfigClusteringInfo(algoritmo="hdbscan")
    motor_hdbscan = FabricaClustering.criar_motor(conf_hdbscan)
    assert isinstance(motor_hdbscan, MotorHDBSCAN)


def test_fabrica_clustering_rejeita_algoritmo_invalido() -> None:
    """Garante lançamento de ErroConfiguracao para algoritmos não suportados."""
    conf_invalida = ConfigClusteringInfo(algoritmo="kmeans")
    conf_invalida.algoritmo = "algoritmo_fantasma"  # type: ignore[assignment]

    with pytest.raises(ErroConfiguracao, match="Algoritmo de clustering .* não suportado"):
        FabricaClustering.criar_motor(conf_invalida)
