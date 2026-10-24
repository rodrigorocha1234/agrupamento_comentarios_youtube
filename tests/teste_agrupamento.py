"""Testes para algoritmos de clustering e catálogo de capacidades."""

import numpy as np
import pytest

from app.agrupamento_modelos.agrupador_dbscan import AgrupadorDbscan
from app.agrupamento_modelos.agrupador_hdbscan import AgrupadorHdbscan
from app.agrupamento_modelos.agrupador_kmeans import AgrupadorKMeans
from app.agrupamento_modelos.fabrica_agrupadores import FabricaAgrupadores


@pytest.fixture
def dados_clusters_sinteticos() -> np.ndarray:
    """Gera dois clusters densos e bem separados."""
    rng = np.random.default_rng(42)
    c1 = rng.normal(loc=0.0, scale=0.2, size=(30, 2))
    c2 = rng.normal(loc=5.0, scale=0.2, size=(30, 2))
    return np.vstack([c1, c2])


def teste_agrupador_kmeans(dados_clusters_sinteticos: np.ndarray) -> None:
    """Verifica treino, predição e centroides do KMeans."""
    kmeans = AgrupadorKMeans(n_clusters=2, random_state=42)
    assert kmeans.capacidades.possui_centroides is True
    assert kmeans.capacidades.suporta_predicao_fora_da_amostra is True
    assert kmeans.capacidades.gera_ruido is False

    rotulos = kmeans.treinar(dados_clusters_sinteticos)
    assert len(rotulos) == 60
    assert set(rotulos) == {0, 1}

    centroides = kmeans.obter_centroides()
    assert centroides is not None
    assert centroides.shape == (2, 2)

    novos_pontos = np.array([[0.1, 0.1], [5.1, 5.1]])
    predicoes = kmeans.predizer(novos_pontos)
    assert len(predicoes) == 2


def teste_agrupador_dbscan(dados_clusters_sinteticos: np.ndarray) -> None:
    """Verifica detecção de ruído e ausência de predict indutivo no DBSCAN."""
    dbscan = AgrupadorDbscan(eps=0.5, min_samples=5)
    assert dbscan.capacidades.possui_centroides is False
    assert dbscan.capacidades.suporta_predicao_fora_da_amostra is False
    assert dbscan.capacidades.gera_ruido is True

    # Adicionar outlier isolado
    dados_com_ruido = np.vstack([dados_clusters_sinteticos, np.array([[50.0, 50.0]])])
    rotulos = dbscan.treinar(dados_com_ruido)

    assert rotulos[-1] == -1  # Ponto distante rotulado como ruído
    assert dbscan.obter_centroides() is None

    with pytest.raises(NotImplementedError):
        dbscan.predizer(np.array([[0.0, 0.0]]))


def teste_agrupador_hdbscan(dados_clusters_sinteticos: np.ndarray) -> None:
    """Verifica treino hierárquico e disponibilidade de probabilidades no HDBSCAN."""
    hdbscan = AgrupadorHdbscan(min_cluster_size=10, min_samples=3)
    rotulos = hdbscan.treinar(dados_clusters_sinteticos)

    assert len(rotulos) == 60
    assert hdbscan.probabilidades is not None
    assert len(hdbscan.probabilidades) == 60


def teste_fabrica_agrupadores() -> None:
    """Valida resolução desacoplada por nome via Registry."""
    fabrica = FabricaAgrupadores()
    k = fabrica.criar_agrupador("kmeans", {"n_clusters": 3})
    d = fabrica.criar_agrupador("dbscan", {"eps": 0.8})
    h = fabrica.criar_agrupador("hdbscan", {"min_cluster_size": 15})

    assert isinstance(k, AgrupadorKMeans)
    assert isinstance(d, AgrupadorDbscan)
    assert isinstance(h, AgrupadorHdbscan)
