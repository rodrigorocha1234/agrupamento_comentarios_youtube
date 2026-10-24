"""Testes para o avaliador estatístico de qualidade de clusters e métricas de ruído."""

import numpy as np
import pytest

from app.avaliacao_modelos.avaliador_clusters import AvaliadorClusters


@pytest.fixture
def dados_duas_bolas() -> tuple[np.ndarray, np.ndarray]:
    """Gera matriz X e rótulos para dois clusters bem definidos."""
    rng = np.random.default_rng(42)
    c1 = rng.normal(loc=0.0, scale=0.1, size=(20, 2))
    c2 = rng.normal(loc=10.0, scale=0.1, size=(20, 2))
    x = np.vstack([c1, c2])
    rotulos = np.array([0] * 20 + [1] * 20, dtype=np.int32)
    return x, rotulos


def teste_avaliacao_clusters_separados(
    dados_duas_bolas: tuple[np.ndarray, np.ndarray],
) -> None:
    """Verifica Silhouette alta e índice Davies-Bouldin baixo para clusters nítidos."""
    matriz_x, rotulos = dados_duas_bolas
    avaliador = AvaliadorClusters()

    relatorio = avaliador.avaliar(matriz_x, rotulos)

    assert relatorio.total_clusters == 2
    assert relatorio.total_ruido == 0
    assert relatorio.proporcao_ruido == 0.0
    assert relatorio.silhouette_global is not None
    assert relatorio.silhouette_global > 0.8
    assert relatorio.davies_bouldin is not None
    assert relatorio.davies_bouldin < 0.3
    assert relatorio.calinski_harabasz is not None
    assert relatorio.calinski_harabasz > 500.0


def teste_avaliacao_com_presenca_de_ruido(
    dados_duas_bolas: tuple[np.ndarray, np.ndarray],
) -> None:
    """Verifica que o avaliador calcula silhouette_sem_ruido de forma transparente."""
    matriz_x, rotulos = dados_duas_bolas
    # Injeta 2 pontos de ruído
    x_ruido = np.vstack([matriz_x, np.array([[5.0, 5.0], [5.0, 6.0]])])
    rotulos_com_ruido = np.array(list(rotulos) + [-1, -1], dtype=np.int32)

    avaliador = AvaliadorClusters()
    relatorio = avaliador.avaliar(x_ruido, rotulos_com_ruido)

    assert relatorio.total_clusters == 2
    assert relatorio.total_ruido == 2
    assert relatorio.proporcao_ruido == pytest.approx(2.0 / 42.0)
    assert relatorio.silhouette_sem_ruido is not None
    assert relatorio.silhouette_sem_ruido > 0.8


def teste_avaliacao_cluster_unico() -> None:
    """Garante que conjunto com apenas 1 cluster reporte None nas métricas sem falha."""
    matriz_x = np.array([[1.0, 2.0], [1.1, 2.1], [0.9, 1.9]])
    rotulos = np.array([0, 0, 0], dtype=np.int32)

    avaliador = AvaliadorClusters()
    relatorio = avaliador.avaliar(matriz_x, rotulos)

    assert relatorio.total_clusters == 1
    assert relatorio.silhouette_global is None
    assert relatorio.davies_bouldin is None
