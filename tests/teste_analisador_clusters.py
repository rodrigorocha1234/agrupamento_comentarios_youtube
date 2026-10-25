"""Testes unitários para o AnalisadorClusters e GeradorVisualizacoesClusters."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.analise_clusters.analisador_clusters import AnalisadorClusters
from app.analise_clusters.gerador_graficos import GeradorVisualizacoesClusters


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
    assert "<title>Relatório Analítico de Clustering</title>" in conteudo
    assert "plotly.js" in conteudo or "cdn.plot.ly" in conteudo
