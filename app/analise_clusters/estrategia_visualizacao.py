"""Interface abstrata (GoF Strategy) para motores de visualização gráfica."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Final

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from app.analise_clusters.analisador_clusters import ResumoAnaliseClusters

if TYPE_CHECKING:
    from app.conf_yaml import ConfigAnalisesInfo

AVISO_PCA: Final[str] = (
    "Projeção meramente exploratória via PCA 2D. Não representa a totalidade da geometria original."
)


class EstrategiaVisualizacao(ABC):
    """Interface abstrata (GoF Strategy) para bibliotecas gráficas (Plotly, Altair, etc.)."""

    @abstractmethod
    def gerar_grafico_pca_2d(
        self,
        matriz_treino: np.ndarray | pd.DataFrame,
        rotulos: list[int],
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure | object:
        """Gera projeção dimensional 2D."""

    @abstractmethod
    def gerar_grafico_distribuicao_clusters(
        self,
        rotulos: list[int],
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure | object:
        """Gera gráfico de distribuição e contagem por cluster."""

    @abstractmethod
    def gerar_boxplot_atributos(
        self,
        dados: pd.DataFrame,
        atributo: str | None = None,
        rotulos: list[int] | None = None,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure | object:
        """Gera diagramas boxplot para comparar a distribuição de atributos."""

    @abstractmethod
    def gerar_grafico_dispersao_2_atributos(
        self,
        dados: pd.DataFrame,
        atributo_x: str | None = None,
        atributo_y: str | None = None,
        rotulos: list[int] | None = None,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure | object:
        """Gera dispersão entre dois atributos reais."""

    @abstractmethod
    def gerar_grafico_perfil_clusters(
        self,
        resumo: ResumoAnaliseClusters,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure | object:
        """Gera comparativo multivariado do perfil médio dos clusters."""

    @abstractmethod
    def gerar_tabela_resumo_clusters(
        self,
        resumo: ResumoAnaliseClusters,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure | object:
        """Produz tabela interativa consolidando estatísticas e métricas de negócio."""

    @abstractmethod
    def exportar_relatorio_html(
        self,
        figuras: list[go.Figure | object],
        caminho_saida: str | Path,
        titulo: str | None = None,
        subtitulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> None:
        """Salva coleção de figuras em relatório HTML autocontido."""
