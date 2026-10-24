"""Testes unitários rigorosos para a fase de clusterização comparativa."""

from pathlib import Path
import numpy as np

from app.agrupamento_modelos.agrupador_dbscan import AgrupadorDBSCAN
from app.agrupamento_modelos.agrupador_hdbscan import AgrupadorHDBSCAN
from app.agrupamento_modelos.agrupador_kmeans import AgrupadorKMeans
from app.agrupamento_modelos.agrupador_tabular import AgrupadorTabular
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
    assert agrupador.obter_rotulos() == rotulos
    assert len(agrupador.labels_) == 60
    assert (agrupador.labels_ == np.array(rotulos)).all()



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
    assert km.obter_init() == "k-means++"
    assert isinstance(db, AgrupadorDBSCAN)
    assert isinstance(hdb, AgrupadorHDBSCAN)


def test_kmeans_inicializacao_kmeans_plus_plus() -> None:
    """Valida a parametrização explícita do init k-means++ e convergência."""
    rng = np.random.default_rng(123)
    dados = rng.normal(loc=0.0, scale=1.0, size=(30, 4))
    agrupador = AgrupadorKMeans(n_clusters=2, init="k-means++", random_state=42, k_automatico=False)

    assert agrupador.obter_init() == "k-means++"
    rotulos, metricas = agrupador.ajustar_e_agrupar(dados)
    assert len(rotulos) == 30
    assert metricas.quantidade_clusters == 2
    assert agrupador.obter_centroides() is not None


def test_agrupador_tabular_dados_sinteticos() -> None:
    """Valida o AgrupadorTabular em dados puramente numéricos carregados do YAML de exemplo."""
    caminho_yaml = Path(__file__).resolve().parent.parent / "config" / "entradas_tabular_exemplo.yaml"
    config = ProvedorConfiguracao(caminho_yaml).carregar()

    rng = np.random.default_rng(99)
    # 3 clusters numéricos sintéticos em 8 dimensões
    c1 = rng.normal(loc=-10.0, scale=0.5, size=(20, 8))
    c2 = rng.normal(loc=0.0, scale=0.5, size=(20, 8))
    c3 = rng.normal(loc=10.0, scale=0.5, size=(20, 8))
    dados: np.ndarray = np.vstack([c1, c2, c3])

    motor_tabular = AgrupadorTabular(config.processamento)
    resultado = motor_tabular.agrupar_matriz(dados)

    assert resultado.n_amostras == 60
    assert resultado.n_features == 8
    assert resultado.reducao_aplicada is True
    assert "kmeans" in resultado.resultados
    assert "dbscan" in resultado.resultados
    assert "hdbscan" in resultado.resultados

    res_km = resultado.resultados["kmeans"]
    assert len(res_km.rotulos) == 60
    assert res_km.metricas.quantidade_clusters >= 2
    assert res_km.metricas.pontuacao_silhueta is not None
    assert res_km.metricas.pontuacao_silhueta > 0.5
    assert len(res_km.analise_clusters) > 0
    # Como entradas_tabular_exemplo.yaml tem eh_temporal: false, status deve ser ESTATICO
    from app.configuracao_geral.tipos_enumerados import StatusTendencia
    assert res_km.analise_clusters[0].status == StatusTendencia.ESTATICO

    # Teste com análise temporal habilitada via indices_temporais
    from dataclasses import replace
    config_temporal = replace(config.processamento, eh_temporal=True)
    motor_temporal = AgrupadorTabular(config_temporal)
    tempos = list(range(60))
    res_temp = motor_temporal.agrupar_matriz(dados, tecnicas=["kmeans"], indices_temporais=tempos)
    res_km_temp = res_temp.resultados["kmeans"]
    assert len(res_km_temp.analise_clusters) > 0
    assert any(c.status in [StatusTendencia.CRESCENDO, StatusTendencia.DECRESCENDO, StatusTendencia.ESTAVEL, StatusTendencia.NOVO] for c in res_km_temp.analise_clusters)


