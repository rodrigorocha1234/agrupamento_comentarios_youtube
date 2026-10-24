"""Testes unitários para o gerador de gráficos Plotly e painel executivo."""

import json

import pandas as pd

from app.avaliacao_modelos.metricas_estatisticas import ResultadoAvaliacao
from app.visualizacao_dados.gerador_graficos import GeradorGraficos
from app.visualizacao_dados.painel_executivo import PainelExecutivo


def teste_gerador_graficos_json_valido() -> None:
    """Verifica se o gerador produz artefatos gráficos serializáveis em JSON."""
    dados = pd.DataFrame(
        {
            "horas_jogadas": [10.0, 50.0, 100.0, 200.0],
            "votos_up": [1, 5, 10, 20],
            "cluster_id": [0, 0, 1, 1],
            "rotulo_negocio": ["novatos", "novatos", "veteranos", "veteranos"],
        }
    )

    gerador = GeradorGraficos(amostragem_maxima=100)

    # 1. Gráfico de dispersão 2D
    json_dispersao = gerador.gerar_dispersao_2d(
        dados, eixo_x="horas_jogadas", eixo_y="votos_up", colorir_por="cluster_id"
    )
    dados_dispersao = json.loads(json_dispersao)
    assert "data" in dados_dispersao
    assert "layout" in dados_dispersao

    # 2. Gráfico de distribuição
    json_dist = gerador.gerar_distribuicao_clusters(dados)
    dados_dist = json.loads(json_dist)
    assert "data" in dados_dist

    # 3. Perfil de medianas
    json_perfil = gerador.gerar_perfil_atributos(dados)
    dados_perfil = json.loads(json_perfil)
    assert "data" in dados_perfil


def teste_painel_executivo_compilacao_relatorio() -> None:
    """Valida a consolidação de relatórios em Markdown e HTML executivo."""
    metricas = ResultadoAvaliacao(
        total_amostras=200,
        total_clusters=3,
        total_ruido=10,
        proporcao_ruido=0.05,
        silhouette_global=0.62,
        silhouette_sem_ruido=0.68,
        davies_bouldin=0.45,
        calinski_harabasz=450.0,
        tamanhos_clusters={0: 90, 1: 100, -1: 10},
    )

    mapa_rotulos = {
        0: "jogadores_moderados",
        1: "jogadores_hardcore",
        -1: "ruido_estatistico",
    }

    painel = PainelExecutivo()
    md = painel.compilar_relatorio_markdown(
        metricas=metricas,
        nome_algoritmo="kmeans",
        mapa_rotulos_negocio=mapa_rotulos,
    )

    assert "# Relatório Executivo de Agrupamento" in md
    assert "jogadores_hardcore" in md
    assert "0.6200" in md

    html = painel.compilar_relatorio_html(
        relatorio_markdown=md,
        graficos_json={"Dispersão": "{}"},
    )

    assert "<!DOCTYPE html>" in html
    assert "Plotly.newPlot" in html
