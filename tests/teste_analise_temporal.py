"""Testes unitários dedicados para a Análise Temporal dos agrupamentos."""

from unittest.mock import MagicMock

import pandas as pd
import plotly.graph_objects as go

from app.analise_clusters.estrategia_altair import EstrategiaVisualizacaoAltair
from app.analise_clusters.estrategia_plotly import EstrategiaVisualizacaoPlotly
from app.analise_temporal.contratos import (
    AlertaPicoTemporal,
    PontoTemporalCluster,
    ResumoAnaliseTemporal,
)
from app.analise_temporal.detector_anomalias import DetectorAnomaliasTemporais
from app.analise_temporal.estrategia_agregacao import (
    AgregadorAnual,
    AgregadorDiario,
    AgregadorMensal,
    AgregadorSemanal,
)
from app.analise_temporal.fabrica_analise_temporal import FabricaAnaliseTemporal
from app.conf_yaml import (
    ConfigAlgoritmosClustering,
    ConfigAnaliseTemporalInfo,
    ConfigAtributosInfo,
    ConfigClusteringInfo,
    ConfigDeteccaoPicosInfo,
    ConfigFonteInfo,
    ConfigParametrosKMeans,
    ConfigPreprocessamentoInfo,
    ConfigProcessamentoInfo,
    ConfigTreinoAtributos,
)
from app.contratos.fonte_dados import ProtocoloFonteDados
from app.contratos.repositorio import ProtocoloRepositorioLakehouse
from app.fachada_pipeline import FachadaPipelineClustering


def test_estrategias_agregacao_temporal() -> None:
    """Verifica conversão de timestamps Unix nas estratégias de granularidade."""
    # Timestamps aproximados para 2024-01-15 12:00:00 UTC (1705320000) e 2024-02-20 (1708430400)
    timestamps = pd.Series([1705320000, 1708430400, None, -1])

    mensal = AgregadorMensal()
    periodos_m = mensal.normalizar_periodos(timestamps)
    assert periodos_m.iloc[0] == "2024-01"
    assert periodos_m.iloc[1] == "2024-02"
    assert periodos_m.iloc[2] == "Desconhecido"
    assert mensal.obter_nome_granularidade() == "mensal"

    semanal = AgregadorSemanal()
    periodos_s = semanal.normalizar_periodos(timestamps)
    assert "2024-W" in periodos_s.iloc[0]
    assert semanal.obter_nome_granularidade() == "semanal"

    diario = AgregadorDiario()
    periodos_d = diario.normalizar_periodos(timestamps)
    assert periodos_d.iloc[0] == "2024-01-15"
    assert diario.obter_nome_granularidade() == "diaria"

    anual = AgregadorAnual()
    periodos_a = anual.normalizar_periodos(timestamps)
    assert periodos_a.iloc[0] == "2024"
    assert anual.obter_nome_granularidade() == "anual"


def test_detector_anomalias_picos() -> None:
    """Verifica detecção de picos atípicos quando o volume desvia da média histórica."""
    config = ConfigDeteccaoPicosInfo(habilitado=True, limiar_desvio_padrao=2.0, minimo_amostras_periodo=5)
    detector = DetectorAnomaliasTemporais(config)

    # 8 períodos normais (volume ~10) e 1 período com pico (volume = 100)
    pontos = [
        PontoTemporalCluster(f"2024-0{i}", 0, "Cluster 0", 10 + (i % 2), 0.5)
        for i in range(1, 9)
    ]
    pontos.append(PontoTemporalCluster("2024-09", 0, "Cluster 0", 100, 0.9))  # Pico extremo!

    alertas = detector.detectar_picos(pontos)
    assert len(alertas) == 1
    assert alertas[0].periodo == "2024-09"
    assert alertas[0].id_cluster == 0
    assert alertas[0].z_score >= 2.0
    assert "Pico de avaliações no período 2024-09" in alertas[0].descricao


def test_analisador_temporal_processamento_completo() -> None:
    """Verifica agregação, preenchimento de ausências e métricas por período."""
    dados = pd.DataFrame(
        {
            "timestamp_created": [
                1705320000,  # Jan 2024
                1705325000,  # Jan 2024
                1708430400,  # Fev 2024
                1708435000,  # Fev 2024
            ],
            "voted_up": [True, False, True, True],
            "playtime_forever": [60.0, 120.0, 180.0, 240.0],
        }
    )
    rotulos = [0, 1, 0, 0]

    cfg = ConfigAnaliseTemporalInfo(
        habilitado=True,
        granularidade="mensal",
        preencher_periodos_ausentes=True,
    )
    analisador = FabricaAnaliseTemporal.criar_analisador(cfg)
    resumo = analisador.analisar(dados, rotulos)

    assert resumo.total_amostras_temporais == 4
    assert resumo.periodos_ordenados == ["2024-01", "2024-02"]
    assert resumo.clusters_presentes == [0, 1]

    # Cluster 0 em Jan: 1 amostra de 2 -> prop = 0.5, voted_up = 1.0 (True)
    ponto_c0_jan = next(p for p in resumo.pontos_temporais if p.periodo == "2024-01" and p.id_cluster == 0)
    assert ponto_c0_jan.quantidade_amostras == 1
    assert ponto_c0_jan.proporcao_periodo == 0.5
    assert ponto_c0_jan.taxa_recomendacao == 1.0
    assert ponto_c0_jan.media_horas_jogadas == 1.0

    # Cluster 1 em Fev: preenchido com 0 amostras
    ponto_c1_fev = next(p for p in resumo.pontos_temporais if p.periodo == "2024-02" and p.id_cluster == 1)
    assert ponto_c1_fev.quantidade_amostras == 0
    assert ponto_c1_fev.proporcao_periodo == 0.0


def test_analisador_temporal_resiliencia_dados_ausentes() -> None:
    """Verifica que o analisador temporal é tolerante a dados vazios ou colunas faltantes."""
    analisador = FabricaAnaliseTemporal.criar_analisador()

    # DataFrame vazio
    resumo_vazio = analisador.analisar(pd.DataFrame(), [])
    assert resumo_vazio.total_amostras_temporais == 0
    assert resumo_vazio.pontos_temporais == []

    # Sem coluna de timestamp
    df_sem_tempo = pd.DataFrame({"coluna_qualquer": [1, 2, 3]})
    resumo_sem_tempo = analisador.analisar(df_sem_tempo, [0, 1, 0])
    assert resumo_sem_tempo.total_amostras_temporais == 0


def test_visualizacoes_temporais_plotly_e_altair() -> None:
    """Verifica a geração de figuras temporais tanto para Plotly quanto para Altair."""
    resumo = ResumoAnaliseTemporal(
        pontos_temporais=[
            PontoTemporalCluster("2024-01", 0, "Cluster 0", 10, 0.5),
            PontoTemporalCluster("2024-01", 1, "Cluster 1", 10, 0.5),
            PontoTemporalCluster("2024-02", 0, "Cluster 0", 20, 0.67),
            PontoTemporalCluster("2024-02", 1, "Cluster 1", 10, 0.33),
        ],
        periodos_ordenados=["2024-01", "2024-02"],
        clusters_presentes=[0, 1],
        alertas_picos=[
            AlertaPicoTemporal(
                periodo="2024-02",
                id_cluster=0,
                nome_rotulo="Cluster 0",
                tipo_alerta="pico_volume",
                z_score=2.5,
                valor_observado=20.0,
                media_historica=15.0,
                descricao="Alerta de teste",
            )
        ],
    )

    # 1. Plotly
    est_plotly = EstrategiaVisualizacaoPlotly()
    fig_evolucao = est_plotly.gerar_grafico_evolucao_temporal(resumo)
    assert isinstance(fig_evolucao, go.Figure)
    assert len(tuple(fig_evolucao.data)) == 2  # 2 clusters

    fig_area = est_plotly.gerar_grafico_area_empilhada_temporal(resumo)
    assert isinstance(fig_area, go.Figure)
    assert len(tuple(fig_area.data)) == 2

    # 2. Altair
    est_altair = EstrategiaVisualizacaoAltair()
    spec_evolucao = est_altair.gerar_grafico_evolucao_temporal(resumo)
    assert isinstance(spec_evolucao, dict)
    assert spec_evolucao["mark"] == "line"

    spec_area = est_altair.gerar_grafico_area_empilhada_temporal(resumo)
    assert isinstance(spec_area, dict)
    assert spec_area["mark"] == "area"


def test_fachada_com_analise_temporal_habilitada() -> None:
    """Verifica que a fachada orquestra a análise temporal e adiciona os gráficos quando habilitada."""
    repo_mock = MagicMock(spec=ProtocoloRepositorioLakehouse)
    dados_bronze = pd.DataFrame(
        {
            "recommendationid": [f"rec_{i}" for i in range(10)],
            "review": [f"texto {i}" for i in range(10)],
            "voted_up": [i % 2 == 0 for i in range(10)],
            "votes_up": [float(i) for i in range(10)],
            "author_playtime_forever": [float((i + 1) * 60) for i in range(10)],
            "timestamp_created": [1705320000 + (i * 86400 * 10) for i in range(10)],
        }
    )
    repo_mock.ler_bronze.return_value = dados_bronze
    repo_mock.gravar_silver.return_value = "s3://silver"
    repo_mock.gravar_gold.return_value = "s3://gold"

    fonte_mock = MagicMock(spec=ProtocoloFonteDados)

    config_fonte = ConfigFonteInfo(tipo="steam_api")
    config_proc = ConfigProcessamentoInfo(motor="pandas")
    config_atrib = ConfigAtributosInfo(
        identificadores=["recommendationid"],
        treino=ConfigTreinoAtributos(colunas=["votes_up", "author_playtime_forever"]),
    )
    config_preproc = ConfigPreprocessamentoInfo()
    config_clust = ConfigClusteringInfo(
        algoritmo="kmeans",
        algoritmos=ConfigAlgoritmosClustering(
            kmeans=ConfigParametrosKMeans(n_clusters=2),
        ),
    )
    config_temporal = ConfigAnaliseTemporalInfo(habilitado=True)

    fachada = FachadaPipelineClustering(
        config_fonte=config_fonte,
        config_processamento=config_proc,
        config_atributos=config_atrib,
        config_preprocessamento=config_preproc,
        config_clustering=config_clust,
        config_analise_temporal=config_temporal,
        repositorio_lakehouse=repo_mock,
        fonte_dados=fonte_mock,
    )

    resultado = fachada.executar(identificador=730)

    assert resultado.sucesso is True
    assert resultado.resumo_temporal is not None
    assert resultado.resumo_temporal.total_amostras_temporais == 10
    assert "evolucao_temporal" in resultado.figuras_geradas
    assert "area_empilhada_temporal" in resultado.figuras_geradas
