"""Testes unitários rigorosos para a fase de clusterização comparativa."""

from pathlib import Path
import numpy as np

from app.agrupamento_modelos.agrupador_dbscan import AgrupadorDBSCAN
from app.agrupamento_modelos.agrupador_hdbscan import AgrupadorHDBSCAN
from app.agrupamento_modelos.agrupador_kmeans import AgrupadorKMeans
from app.agrupamento_modelos.fabrica_agrupadores import FabricaAgrupadores
from app.configuracao_geral.provedor_configuracao import ProvedorConfiguracao


def test_kmeans_agrupamento_e_metricas() -> None:
    """Verifica convergência do KMeans, centróides e métricas de silhueta."""
    rng = np.random.default_rng(42)
    c1 = rng.normal(loc=-5.0, scale=0.5, size=(20, 5))
    c2 = rng.normal(loc=0.0, scale=0.5, size=(20, 5))
    c3 = rng.normal(loc=5.0, scale=0.5, size=(20, 5))
    dados: np.ndarray = np.vstack([c1, c2, c3])

    agrupador = AgrupadorKMeans(n_clusters=3, random_state=42, k_automatico=False)
    rotulos, metricas = agrupador.ajustar_e_agrupar(dados)

    assert len(rotulos) == 60
    assert metricas.quantidade_clusters == 3
    assert metricas.fracao_ruido == 0.0
    assert metricas.pontuacao_silhueta is not None
    assert metricas.pontuacao_silhueta > 0.4
    assert agrupador.obter_centroides() is not None
    assert agrupador.obter_modelo() is not None


def test_kmeans_selecao_automatica_k_otimo() -> None:
    """Valida a identificação autônoma do número de clusters (k ótimo) pelo Silhouette Score."""
    rng = np.random.default_rng(42)
    # Cria exatamente 3 clusters densos e bem espaçados
    c1 = rng.normal(loc=-15.0, scale=0.3, size=(25, 4))
    c2 = rng.normal(loc=0.0, scale=0.3, size=(25, 4))
    c3 = rng.normal(loc=15.0, scale=0.3, size=(25, 4))
    dados: np.ndarray = np.vstack([c1, c2, c3])

    agrupador = AgrupadorKMeans(k_automatico=True, k_min=2, k_max=6, random_state=42)
    rotulos, metricas = agrupador.ajustar_e_agrupar(dados)

    assert len(rotulos) == 75
    # O k ótimo selecionado autonomamente deve ser 3
    assert agrupador.obter_k_otimo() == 3
    assert metricas.quantidade_clusters == 3
    assert metricas.pontuacao_silhueta is not None
    assert metricas.pontuacao_silhueta > 0.8
    assert agrupador.obter_modelo() is not None
    assert len(agrupador.obter_historico_k()) >= 2


def test_kmeans_fallback_com_poucas_amostras() -> None:
    """Verifica comportamento defensivo para matriz com apenas 2 amostras."""
    dados = np.array([[1.0, 2.0], [3.0, 4.0]])
    agrupador = AgrupadorKMeans(k_automatico=True, k_min=2, k_max=5)
    rotulos, _ = agrupador.ajustar_e_agrupar(dados)

    assert len(rotulos) == 2
    assert agrupador.obter_modelo() is not None


def test_dbscan_com_deteccao_de_ruido() -> None:
    """Verifica se o DBSCAN rotula outliers isolados como ruído (-1)."""
    rng = np.random.default_rng(42)
    c1 = rng.normal(loc=-2.0, scale=0.2, size=(20, 2))
    c2 = rng.normal(loc=2.0, scale=0.2, size=(20, 2))
    outliers = np.array([[100.0, 100.0], [-100.0, -100.0]])
    dados_com_ruido: np.ndarray = np.vstack([c1, c2, outliers])

    agrupador = AgrupadorDBSCAN(eps=1.0, min_samples=3, metric="euclidean")
    rotulos, metricas = agrupador.ajustar_e_agrupar(dados_com_ruido)

    assert len(rotulos) == 42
    assert -1 in rotulos
    assert metricas.fracao_ruido > 0.0


def test_hdbscan_probabilidades_e_densidade() -> None:
    """Testa agrupamento HDBSCAN e verificação de probabilidades."""
    rng = np.random.default_rng(42)
    c1 = rng.normal(loc=-5.0, scale=0.4, size=(25, 3))
    c2 = rng.normal(loc=5.0, scale=0.4, size=(25, 3))
    dados: np.ndarray = np.vstack([c1, c2])

    agrupador = AgrupadorHDBSCAN(min_cluster_size=5, min_samples=3)
    rotulos, metricas = agrupador.ajustar_e_agrupar(dados)

    assert len(rotulos) == 50
    assert metricas.quantidade_clusters >= 1
    assert agrupador.obter_probabilidades() is not None


def test_fabrica_agrupadores_instancia_tecnicas() -> None:
    """Testa se a factory instancia corretamente KMeans, DBSCAN e HDBSCAN."""
    caminho_yaml = Path(__file__).resolve().parent.parent / "config" / "entradas.yaml"
    config = ProvedorConfiguracao(caminho_yaml).carregar()

    km = FabricaAgrupadores.criar_agrupador("kmeans", config.processamento)
    db = FabricaAgrupadores.criar_agrupador("dbscan", config.processamento)
    hdb = FabricaAgrupadores.criar_agrupador("hdbscan", config.processamento)

    assert isinstance(km, AgrupadorKMeans)
    assert isinstance(db, AgrupadorDBSCAN)
    assert isinstance(hdb, AgrupadorHDBSCAN)
