"""Módulo de geração de visualizações analíticas interativas com Plotly."""

from collections import Counter
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.decomposition import PCA

AVISO_PCA: Final[str] = (
    "Projeção meramente exploratória via PCA 2D. Não representa a totalidade da geometria original."
)


class GeradorVisualizacoesClusters:
    """Produz figuras interativas Plotly para diagnóstico visual e relatórios analíticos."""

    @staticmethod
    def gerar_grafico_pca_2d(
        matriz_treino: np.ndarray | pd.DataFrame,
        rotulos: list[int],
        titulo: str = "Projeção Exploratória dos Agrupamentos (PCA 2D)",
    ) -> go.Figure:
        """Gera gráfico de dispersão 2D via PCA com rotulagem dos clusters."""
        if isinstance(matriz_treino, pd.DataFrame):
            matriz_np = np.asarray(matriz_treino.to_numpy(dtype=np.float64), dtype=np.float64)
        else:
            matriz_np = np.asarray(matriz_treino, dtype=np.float64)

        n_colunas = matriz_np.shape[1]
        if n_colunas < 2:
            comp_1 = matriz_np[:, 0]
            comp_2 = np.zeros_like(comp_1)
        else:
            pca = PCA(n_components=2, random_state=42)
            projetado = pca.fit_transform(matriz_np)
            comp_1 = projetado[:, 0]
            comp_2 = projetado[:, 1]

        fig = go.Figure()
        rotulos_unicos = sorted(set(rotulos))

        for r in rotulos_unicos:
            idx = [i for i, val in enumerate(rotulos) if val == r]
            nome = "Ruído (-1)" if r == -1 else f"Cluster {r}"
            cor = "#888888" if r == -1 else None

            fig.add_trace(
                go.Scatter(
                    x=comp_1[idx],
                    y=comp_2[idx],
                    mode="markers",
                    name=nome,
                    marker={"size": 7, "opacity": 0.8, "color": cor},
                    text=[f"Amostra {i} | {nome}" for i in idx],
                    hoverinfo="text+x+y",
                )
            )

        fig.update_layout(
            title=titulo,
            xaxis_title="Componente Principal 1",
            yaxis_title="Componente Principal 2",
            template="plotly_white",
            annotations=[
                {
                    "text": AVISO_PCA,
                    "showarrow": False,
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": -0.15,
                    "font": {"size": 10, "color": "gray"},
                }
            ],
        )
        return fig

    @staticmethod
    def gerar_grafico_distribuicao_clusters(
        rotulos: list[int],
        titulo: str = "Distribuição de Amostras por Cluster",
    ) -> go.Figure:
        """Gera gráfico de barras com a contagem absoluta e percentual por cluster."""
        contagem = Counter(rotulos)
        total = len(rotulos) if rotulos else 1

        clusters = sorted(contagem.keys())
        nomes = ["Ruído (-1)" if c == -1 else f"Cluster {c}" for c in clusters]
        valores = [contagem[c] for c in clusters]
        percentuais = [f"{(v / total) * 100:.1f}%" for v in valores]

        cores = ["#e74c3c" if c == -1 else "#3498db" for c in clusters]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=nomes,
                    y=valores,
                    text=percentuais,
                    textposition="auto",
                    marker_color=cores,
                )
            ]
        )

        fig.update_layout(
            title=titulo,
            xaxis_title="Agrupamento",
            yaxis_title="Quantidade de Avaliações",
            template="plotly_white",
        )
        return fig

    @staticmethod
    def gerar_boxplot_atributos(
        dados: pd.DataFrame,
        atributo: str,
        rotulos: list[int],
        titulo: str | None = None,
    ) -> go.Figure:
        """Gera diagramas boxplot para comparar a distribuição de um atributo específico."""
        if atributo not in dados.columns or len(dados) != len(rotulos):
            return go.Figure()

        df_aux = pd.DataFrame(
            {
                "valor": dados[atributo].to_numpy(dtype=np.float64),
                "cluster": ["Ruído (-1)" if r == -1 else f"Cluster {r}" for r in rotulos],
            }
        )

        fig = go.Figure()
        for grupo in sorted(df_aux["cluster"].unique()):
            sub = df_aux[df_aux["cluster"] == grupo]
            fig.add_trace(
                go.Box(
                    y=sub["valor"],
                    name=grupo,
                    boxmean=True,
                )
            )

        titulo_final = titulo or f"Distribuição de '{atributo}' por Cluster"
        fig.update_layout(
            title=titulo_final,
            yaxis_title=atributo,
            xaxis_title="Cluster",
            template="plotly_white",
        )
        return fig

    @staticmethod
    def exportar_relatorio_html(
        figuras: list[go.Figure],
        caminho_saida: str | Path,
    ) -> None:
        """Salva uma coleção de figuras Plotly consolidadas em arquivo HTML autocontido."""
        caminho = Path(caminho_saida)
        caminho.parent.mkdir(parents=True, exist_ok=True)

        blocos_html: list[str] = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'/>",
            "<title>Relatório Analítico de Clustering</title>",
            "<style>body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 30px; background-color: #f8f9fa; } .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }</style>",
            "</head>",
            "<body>",
            "<h1>Relatório Analítico de Agrupamento de Avaliações</h1>",
            "<p>Diagnósticos visuais, distribuição de grupos e projeções multidimensionais.</p>",
        ]

        for i, fig in enumerate(figuras):
            include_js = i == 0
            div_html = fig.to_html(full_html=False, include_plotlyjs="cdn" if include_js else False)
            blocos_html.append(f"<div class='card'>{div_html}</div>")

        blocos_html.append("</body></html>")
        caminho.write_text("\n".join(blocos_html), encoding="utf-8")
