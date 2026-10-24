"""Gerador desacoplado de gráficos e artefatos visuais com backend Plotly."""

from collections.abc import Sequence
from typing import final

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


@final
class GeradorGraficos:
    """Produz artefatos gráficos serializados em formato JSON ou HTML autônomo."""

    def __init__(self, amostragem_maxima: int = 5000, random_state: int = 42) -> None:
        self._amostragem_maxima = amostragem_maxima
        self._random_state = random_state

    def gerar_dispersao_2d(
        self,
        dados: pd.DataFrame,
        eixo_x: str,
        eixo_y: str,
        colorir_por: str = "cluster_id",
        titulo: str = "Dispersão 2D de Clusters",
    ) -> str:
        """Gera gráfico de dispersão 2D interativo com cores por cluster."""
        df_amostra = self._amostrar_se_necessario(dados)

        col_x = eixo_x if eixo_x in df_amostra.columns else df_amostra.columns[0]
        col_y = eixo_y if eixo_y in df_amostra.columns else df_amostra.columns[1]
        col_cor = colorir_por if colorir_por in df_amostra.columns else None

        fig = px.scatter(
            df_amostra,
            x=col_x,
            y=col_y,
            color=col_cor,
            title=titulo,
            hover_data=[
                c
                for c in ["recommendationid", "rotulo_negocio"]
                if c in df_amostra.columns
            ],
        )
        return str(fig.to_json())

    def gerar_distribuicao_clusters(
        self,
        dados: pd.DataFrame,
        coluna_cluster: str = "cluster_id",
        titulo: str = "Distribuição de Reviews por Cluster",
    ) -> str:
        """Gera gráfico de barras com volumetria e percentual por cluster."""
        if coluna_cluster not in dados.columns:
            fig_vazia = go.Figure()
            return str(fig_vazia.to_json())

        serie_contagens = dados[coluna_cluster].value_counts().sort_index()
        contagens = pd.DataFrame(
            {
                "cluster": list(serie_contagens.index),
                "quantidade": list(serie_contagens.values),
            }
        )

        def _formatar_rotulo(c: object) -> str:
            return "Ruído (-1)" if str(c) == "-1" else f"Cluster {c}"

        contagens["rotulo_exibicao"] = contagens["cluster"].map(_formatar_rotulo)

        fig = px.bar(
            contagens,
            x="rotulo_exibicao",
            y="quantidade",
            color="rotulo_exibicao",
            title=titulo,
            labels={"quantidade": "Número de Reviews", "rotulo_exibicao": "Cluster"},
        )
        return str(fig.to_json())

    def gerar_perfil_atributos(
        self,
        dados: pd.DataFrame,
        coluna_cluster: str = "cluster_id",
        atributos: Sequence[str] | None = None,
        titulo: str = "Perfil dos Atributos por Cluster (Medianas)",
    ) -> str:
        """Gera gráfico de perfil comparativo das medianas dos atributos por cluster."""
        if coluna_cluster not in dados.columns or dados.empty:
            return str(go.Figure().to_json())

        colunas_validas = [
            c
            for c in (atributos or dados.select_dtypes(include="number").columns)
            if c in dados.columns and c != coluna_cluster
        ]

        if not colunas_validas:
            return str(go.Figure().to_json())

        agrupado = dados.groupby(coluna_cluster)[colunas_validas].median().reset_index()
        melted = agrupado.melt(
            id_vars=[coluna_cluster],
            value_vars=colunas_validas,
            var_name="atributo",
            value_name="mediana",
        )
        melted["cluster_str"] = melted[coluna_cluster].astype(str)

        fig = px.bar(
            melted,
            x="atributo",
            y="mediana",
            color="cluster_str",
            barmode="group",
            title=titulo,
        )
        return str(fig.to_json())

    def _amostrar_se_necessario(self, dados: pd.DataFrame) -> pd.DataFrame:
        """Aplica amostragem determinística se o volume exceder o limite de renderização."""
        if len(dados) <= self._amostragem_maxima:
            return dados.copy()
        return dados.sample(n=self._amostragem_maxima, random_state=self._random_state)
