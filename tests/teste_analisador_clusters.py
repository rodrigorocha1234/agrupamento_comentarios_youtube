"""Testes unitários para o AnalisadorClusters e GeradorVisualizacoesClusters."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.analise_clusters.analisador_clusters import (
    AnalisadorClusters,
    ResumoAnaliseClusters,
)
from app.analise_clusters.gerador_graficos import (
    EstrategiaVisualizacao,
    EstrategiaVisualizacaoAltair,
    EstrategiaVisualizacaoPlotly,
    FabricaVisualizacoes,
    FiguraAnalitica,
    GeradorVisualizacoesClusters,
)
from app.analise_temporal.contratos import ResumoAnaliseTemporal
from app.conf_yaml import (
    ConfigAmostrasAnalises,
    ConfigAnalisesInfo,
    ConfigMetricaResumo,
)
from app.excecoes import ErroConfiguracao


@pytest.fixture
def dados_analise_sinteticos() -> tuple[pd.DataFrame, list[int], pd.DataFrame, np.ndarray]:
    """Gera matriz com 2 clusters e ruído (-1), metadados e centroides sintéticos."""
    matriz = pd.DataFrame(
        {
            "attr_1": [1.0, 1.2, 0.9, 10.0, 10.5, 9.8, -50.0],
            "attr_2": [2.0, 2.1, 1.9, 20.0, 20.2, 19.9, 100.0],
        }
    )
    rotulos = [0, 0, 0, 1, 1, 1, -1]
    metadados = pd.DataFrame(
        {
            "recommendationid": [f"id_{i}" for i in range(7)],
            "review": [f"review teste {i}" for i in range(7)],
            "voted_up": [True, True, False, False, False, True, False],
            "author_playtime_forever": [120, 180, 240, 600, 720, 840, 30],
        }
    )
    centroides = np.array(
        [
            [1.033, 2.0],
            [10.1, 20.033],
        ],
        dtype=np.float64,
    )
    return matriz, rotulos, metadados, centroides


def test_gerar_resumo_estatistico_com_ruido_e_centroides(
    dados_analise_sinteticos: tuple[pd.DataFrame, list[int], pd.DataFrame, np.ndarray],
) -> None:
    """Verifica que o resumo agrega médias, medianas, taxa de recomendação e centroides."""
    matriz, rotulos, metadados, centroides = dados_analise_sinteticos

    resumo = AnalisadorClusters.gerar_resumo_estatistico(
        matriz_treino=matriz,
        rotulos=rotulos,
        metadados=metadados,
        centroides=centroides,
    )

    assert resumo.total_amostras == 7
    assert resumo.quantidade_clusters_validos == 2
    assert resumo.quantidade_ruido == 1
    assert pytest.approx(resumo.proporcao_ruido, rel=1e-2) == 1.0 / 7.0
    assert len(resumo.perfis) == 3

    perfil_ruido = next(p for p in resumo.perfis if p.id_cluster == -1)
    assert perfil_ruido.nome_rotulo == "Ruído / Outlier"
    assert perfil_ruido.quantidade_amostras == 1
    assert perfil_ruido.distancia_media_centroide is None

    perfil_c0 = next(p for p in resumo.perfis if p.id_cluster == 0)
    assert perfil_c0.quantidade_amostras == 3
    assert perfil_c0.distancia_media_centroide is not None
    assert perfil_c0.distancia_media_centroide >= 0.0
    assert perfil_c0.taxa_recomendacao is not None
    assert pytest.approx(perfil_c0.taxa_recomendacao, rel=1e-2) == 2.0 / 3.0
    assert perfil_c0.media_horas_jogadas == 3.0  # (120+180+240)/3 = 180 min = 3h


def test_gerar_resumo_estatistico_vazio() -> None:
    """Verifica que matriz vazia retorna resumo com zeros sem disparar exceção."""
    resumo = AnalisadorClusters.gerar_resumo_estatistico(
        matriz_treino=np.zeros((0, 2)),
        rotulos=[],
    )
    assert resumo.total_amostras == 0
    assert resumo.quantidade_clusters_validos == 0
    assert len(resumo.perfis) == 0


def test_extrair_amostras_reviews_por_cluster(
    dados_analise_sinteticos: tuple[pd.DataFrame, list[int], pd.DataFrame, np.ndarray],
) -> None:
    """Verifica extração de amostras das reviews originais para inspeção humana."""
    _, rotulos, metadados, _ = dados_analise_sinteticos

    amostras = AnalisadorClusters.extrair_amostras_reviews_por_cluster(
        metadados=metadados,
        rotulos=rotulos,
        amostras_por_cluster=2,
    )

    assert -1 in amostras
    assert 0 in amostras
    assert 1 in amostras
    assert len(amostras[0]) == 2
    assert "review" in amostras[0][0]
    assert "recommendationid" in amostras[0][0]


def test_gerador_visualizacoes_e_exportacao_html(
    dados_analise_sinteticos: tuple[pd.DataFrame, list[int], pd.DataFrame, np.ndarray],
    tmp_path: Path,
) -> None:
    """Verifica criação de gráficos Plotly e geração do HTML consolidado."""
    matriz, rotulos, _metadados, _ = dados_analise_sinteticos

    fig_pca = GeradorVisualizacoesClusters.gerar_grafico_pca_2d(matriz, rotulos)
    assert fig_pca is not None
    assert len(tuple(fig_pca.data)) == 3

    fig_dist = GeradorVisualizacoesClusters.gerar_grafico_distribuicao_clusters(rotulos)
    assert fig_dist is not None

    fig_box = GeradorVisualizacoesClusters.gerar_boxplot_atributos(matriz, "attr_1", rotulos)
    assert fig_box is not None

    arquivo_saida = tmp_path / "relatorio.html"
    GeradorVisualizacoesClusters.exportar_relatorio_html(
        figuras=[fig_pca, fig_dist, fig_box],
        caminho_saida=arquivo_saida,
    )

    assert arquivo_saida.exists()
    conteudo = arquivo_saida.read_text(encoding="utf-8")
    assert "<title>Relatório Analítico" in conteudo
    assert "plotly.js" in conteudo or "cdn.plot.ly" in conteudo


def test_gerador_visualizacoes_dispersao_perfil_resumo(
    dados_analise_sinteticos: tuple[pd.DataFrame, list[int], pd.DataFrame, np.ndarray],
) -> None:
    """Verifica geração dos gráficos de dispersão 2D entre atributos, perfil e tabela resumo."""
    matriz, rotulos, metadados, centroides = dados_analise_sinteticos

    resumo = AnalisadorClusters.gerar_resumo_estatistico(
        matriz_treino=matriz,
        rotulos=rotulos,
        metadados=metadados,
        centroides=centroides,
    )

    # 1. Dispersão entre 2 atributos reais
    fig_disp = GeradorVisualizacoesClusters.gerar_grafico_dispersao_2_atributos(
        dados=matriz,
        atributo_x="attr_1",
        atributo_y="attr_2",
        rotulos=rotulos,
    )
    assert fig_disp is not None
    assert len(tuple(fig_disp.data)) == 3  # Cluster 0, Cluster 1, Ruído (-1)
    assert fig_disp.layout.xaxis.title.text == "attr_1"
    assert fig_disp.layout.yaxis.title.text == "attr_2"

    # 2. Perfil médio dos clusters
    fig_perfil = GeradorVisualizacoesClusters.gerar_grafico_perfil_clusters(resumo)
    assert fig_perfil is not None
    assert len(tuple(fig_perfil.data)) == 3  # 3 perfis/clusters

    # 3. Tabela interativa de resumo dos clusters
    fig_resumo = GeradorVisualizacoesClusters.gerar_tabela_resumo_clusters(resumo)
    assert fig_resumo is not None
    assert len(tuple(fig_resumo.data)) == 1
    assert fig_resumo.data[0].to_plotly_json().get("type") == "table"


def test_analisador_clusters_generico_outro_projeto(tmp_path: Path) -> None:
    """Verifica que o analisador aceita configurações customizadas via YAML para outro domínio (ex: YouTube)."""
    # Configuração de métricas, layout e amostras simulando comentários do YouTube
    from app.conf_yaml import ConfigLayoutGraficos, ConfigTabelaResumoGrafico

    config_youtube = ConfigAnalisesInfo(
        layout=ConfigLayoutGraficos(
            titulo_distribuicao="Distribuição de Comentários por Cluster",
            eixo_y_distribuicao="Quantidade de Comentários",
            titulo_relatorio="Relatório Analítico de Comentários do YouTube",
            subtitulo_relatorio="Agrupamento semântico de comentários de vídeos.",
        ),
        tabela_resumo=ConfigTabelaResumoGrafico(
            coluna_quantidade="Qtd Comentários",
        ),
        metricas_resumo=[
            ConfigMetricaResumo(nome="media_likes", coluna="like_count", operacao="media"),
            ConfigMetricaResumo(nome="taxa_sentimento", coluna="is_positive", operacao="proporcao"),
        ],
        amostras=ConfigAmostrasAnalises(
            quantidade_por_cluster=2,
            colunas=["comment_id", "text_original", "author_channel", "like_count"],
        ),
    )

    matriz = pd.DataFrame({"engagement_rate": [0.1, 0.15, 0.8, 0.85]})
    rotulos = [0, 0, 1, 1]
    metadados = pd.DataFrame(
        {
            "comment_id": ["c1", "c2", "c3", "c4"],
            "text_original": ["legal", "muito bom", "ótimo vídeo", "excelente conteúdo"],
            "author_channel": ["ch1", "ch2", "ch3", "ch4"],
            "like_count": [10, 20, 100, 200],
            "is_positive": [True, True, True, True],
        }
    )

    resumo = AnalisadorClusters.gerar_resumo_estatistico(
        matriz_treino=matriz,
        rotulos=rotulos,
        metadados=metadados,
        config_analises=config_youtube,
    )

    assert len(resumo.perfis) == 2
    p0 = resumo.perfis[0]
    p1 = resumo.perfis[1]

    assert p0.metricas_personalizadas["media_likes"] == 15.0
    assert p0.metricas_personalizadas["taxa_sentimento"] == 1.0
    assert p1.metricas_personalizadas["media_likes"] == 150.0

    # Extrai amostras usando a configuração do YAML do YouTube
    amostras = AnalisadorClusters.extrair_amostras_reviews_por_cluster(
        metadados=metadados,
        rotulos=rotulos,
        config_analises=config_youtube,
    )
    assert 0 in amostras
    assert len(amostras[0]) == 2
    assert "comment_id" in amostras[0][0]
    assert "text_original" in amostras[0][0]
    assert "recommendationid" not in amostras[0][0]

    # Valida que os gráficos respeitam os eixos e títulos configurados no YAML
    fig_dist = GeradorVisualizacoesClusters.gerar_grafico_distribuicao_clusters(
        rotulos=rotulos,
        config_analises=config_youtube,
    )
    assert fig_dist.layout.yaxis.title.text == "Quantidade de Comentários"
    assert fig_dist.layout.title.text == "Distribuição de Comentários por Cluster"

    # Valida exportação HTML com cabeçalhos customizados pelo YAML
    arquivo_yt = tmp_path / "relatorio_youtube.html"
    GeradorVisualizacoesClusters.exportar_relatorio_html(
        figuras=[fig_dist],
        caminho_saida=arquivo_yt,
        config_analises=config_youtube,
    )
    assert arquivo_yt.exists()
    conteudo_yt = arquivo_yt.read_text(encoding="utf-8")
    assert "<h1>Relatório Analítico de Comentários do YouTube</h1>" in conteudo_yt
    assert "<p>Agrupamento semântico de comentários de vídeos.</p>" in conteudo_yt


def test_padrao_gof_estrategia_e_fabrica_visualizacoes(tmp_path: Path) -> None:
    """Valida os padrões GoF Strategy e Factory para múltiplos motores gráficos."""
    # 1. Factory criando a estratégia padrão Plotly
    est_plotly = FabricaVisualizacoes.criar_estrategia("plotly")
    assert isinstance(est_plotly, EstrategiaVisualizacaoPlotly)

    # 2. Factory criando a estratégia alternativa Altair
    est_altair = FabricaVisualizacoes.criar_estrategia("altair")
    assert isinstance(est_altair, EstrategiaVisualizacaoAltair)

    # Valida geração funcional com a estratégia Altair
    rotulos = [0, 0, 1, -1]
    chart_altair = est_altair.gerar_grafico_distribuicao_clusters(rotulos=rotulos)
    assert isinstance(chart_altair, dict)
    assert chart_altair.get("mark") == "bar"

    # Exportação de relatório com estratégia Altair
    arq_altair = tmp_path / "altair_relatorio.html"
    est_altair.exportar_relatorio_html([chart_altair], arq_altair)
    assert arq_altair.exists()
    assert "vega-embed" in arq_altair.read_text(encoding="utf-8")

    # 3. Valida extensibilidade: registrar novo motor dinamicamente no runtime
    class EstrategiaCustom(EstrategiaVisualizacao):
        def gerar_grafico_pca_2d(
            self,
            matriz_treino: np.ndarray | pd.DataFrame,
            rotulos: list[int],
            titulo: str | None = None,
            config_analises: ConfigAnalisesInfo | None = None,
        ) -> FiguraAnalitica:
            return {"grafico": "pca_custom"}

        def gerar_grafico_distribuicao_clusters(
            self,
            rotulos: list[int],
            titulo: str | None = None,
            config_analises: ConfigAnalisesInfo | None = None,
        ) -> FiguraAnalitica:
            return {"grafico": "dist_custom"}

        def gerar_boxplot_atributos(
            self,
            dados: pd.DataFrame,
            atributo: str | None = None,
            rotulos: list[int] | None = None,
            titulo: str | None = None,
            config_analises: ConfigAnalisesInfo | None = None,
        ) -> FiguraAnalitica:
            return {"grafico": "box_custom"}

        def gerar_grafico_dispersao_2_atributos(
            self,
            dados: pd.DataFrame,
            atributo_x: str | None = None,
            atributo_y: str | None = None,
            rotulos: list[int] | None = None,
            titulo: str | None = None,
            config_analises: ConfigAnalisesInfo | None = None,
        ) -> FiguraAnalitica:
            return {"grafico": "disp_custom"}

        def gerar_grafico_perfil_clusters(
            self,
            resumo: ResumoAnaliseClusters,
            titulo: str | None = None,
            config_analises: ConfigAnalisesInfo | None = None,
        ) -> FiguraAnalitica:
            return {"grafico": "perfil_custom"}

        def gerar_tabela_resumo_clusters(
            self,
            resumo: ResumoAnaliseClusters,
            titulo: str | None = None,
            config_analises: ConfigAnalisesInfo | None = None,
        ) -> FiguraAnalitica:
            return {"grafico": "tabela_custom"}

        def gerar_grafico_evolucao_temporal(
            self,
            resumo_temporal: ResumoAnaliseTemporal,
            titulo: str | None = None,
            config_analises: ConfigAnalisesInfo | None = None,
        ) -> FiguraAnalitica:
            return {"grafico": "evolucao_custom"}

        def gerar_grafico_area_empilhada_temporal(
            self,
            resumo_temporal: ResumoAnaliseTemporal,
            titulo: str | None = None,
            config_analises: ConfigAnalisesInfo | None = None,
        ) -> FiguraAnalitica:
            return {"grafico": "area_empilhada_custom"}

        def exportar_relatorio_html(
            self,
            figuras: list[FiguraAnalitica],
            caminho_saida: str | Path,
            titulo: str | None = None,
            subtitulo: str | None = None,
            config_analises: ConfigAnalisesInfo | None = None,
        ) -> None:
            pass

    FabricaVisualizacoes.registrar_estrategia("custom_engine", EstrategiaCustom)
    est_custom = FabricaVisualizacoes.criar_estrategia("custom_engine")
    assert isinstance(est_custom, EstrategiaCustom)

    # Contexto com injeção de dependência (Strategy pattern)
    gerador_contexto = GeradorVisualizacoesClusters(estrategia=est_custom)
    assert gerador_contexto.estrategia is est_custom

    # 4. Motor inválido lança ErroConfiguracao
    with pytest.raises(ErroConfiguracao, match="não suportado"):
        FabricaVisualizacoes.criar_estrategia("motor_inexistente_xyz")

