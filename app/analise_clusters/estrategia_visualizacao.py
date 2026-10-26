"""Interface abstrata (GoF Strategy) para motores de visualização gráfica."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Final

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from app.analise_clusters.analisador_clusters import ResumoAnaliseClusters
from app.analise_temporal.contratos import ResumoAnaliseTemporal
from app.contratos.tipos_dados import DicionarioJson

if TYPE_CHECKING:
    from app.conf_yaml import ConfigAnalisesInfo

AVISO_PCA: Final[str] = (
    "Projeção meramente exploratória via PCA 2D. Não representa a totalidade da geometria original."
)

type FiguraAnalitica = go.Figure | DicionarioJson


class EstrategiaVisualizacao(ABC):
    """Interface abstrata (GoF Strategy) para bibliotecas gráficas (Plotly, Altair, etc.)."""

    @abstractmethod
    def gerar_grafico_pca_2d(
        self,
        matriz_treino: np.ndarray | pd.DataFrame,
        rotulos: list[int],
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> FiguraAnalitica:
        """Gera projeção dimensional 2D."""

    @abstractmethod
    def gerar_grafico_distribuicao_clusters(
        self,
        rotulos: list[int],
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> FiguraAnalitica:
        """Gera gráfico de distribuição e contagem por cluster."""

    @abstractmethod
    def gerar_boxplot_atributos(
        self,
        dados: pd.DataFrame,
        atributo: str | None = None,
        rotulos: list[int] | None = None,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> FiguraAnalitica:
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
    ) -> FiguraAnalitica:
        """Gera dispersão entre dois atributos reais."""

    @abstractmethod
    def gerar_grafico_perfil_clusters(
        self,
        resumo: ResumoAnaliseClusters,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> FiguraAnalitica:
        """Gera comparativo multivariado do perfil médio dos clusters."""

    @abstractmethod
    def gerar_tabela_resumo_clusters(
        self,
        resumo: ResumoAnaliseClusters,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> FiguraAnalitica:
        """Produz tabela interativa consolidando estatísticas e métricas de negócio."""

    @abstractmethod
    def gerar_grafico_evolucao_temporal(
        self,
        resumo_temporal: ResumoAnaliseTemporal,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> FiguraAnalitica:
        """Gera gráfico cronológico demonstrando o volume de cada cluster por período."""

    @abstractmethod
    def gerar_grafico_area_empilhada_temporal(
        self,
        resumo_temporal: ResumoAnaliseTemporal,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> FiguraAnalitica:
        """Gera gráfico de área 100% empilhada com a proporção de cada cluster ao longo do tempo."""

    @abstractmethod
    def exportar_relatorio_html(
        self,
        figuras: list[FiguraAnalitica],
        caminho_saida: str | Path,
        titulo: str | None = None,
        subtitulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> None:
        """Salva coleção de figuras em relatório HTML autocontido."""
