"""Módulo de fachada e contexto (GoF Facade/Strategy) para visualizações analíticas."""

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from app.analise_clusters.analisador_clusters import ResumoAnaliseClusters
from app.analise_clusters.estrategia_altair import EstrategiaVisualizacaoAltair
from app.analise_clusters.estrategia_plotly import EstrategiaVisualizacaoPlotly
from app.analise_clusters.estrategia_visualizacao import (
    AVISO_PCA,
    EstrategiaVisualizacao,
)
from app.analise_clusters.fabrica_visualizacoes import FabricaVisualizacoes

if TYPE_CHECKING:
    from app.conf_yaml import ConfigAnalisesInfo

__all__ = [
    "AVISO_PCA",
    "EstrategiaVisualizacao",
    "EstrategiaVisualizacaoAltair",
    "EstrategiaVisualizacaoPlotly",
    "FabricaVisualizacoes",
    "GeradorVisualizacoesClusters",
]


class GeradorVisualizacoesClusters:
    """Fachada e Contexto (GoF Strategy/Facade) para diagnósticos visuais e relatórios."""

    def __init__(self, estrategia: EstrategiaVisualizacao | None = None) -> None:
        """Permite instanciar com uma estratégia específica via injeção de dependência."""
        self._estrategia: EstrategiaVisualizacao = estrategia or EstrategiaVisualizacaoPlotly()

    @property
    def estrategia(self) -> EstrategiaVisualizacao:
        """Retorna a estratégia de visualização ativa nesta instância."""
        return self._estrategia

    @classmethod
    def _obter_config_analises_padrao(cls) -> "ConfigAnalisesInfo | None":
        """Carrega a configuração de análises padrão a partir do YAML do projeto se existir."""
        try:
            from app.conf_yaml import ConfigAnalisesInfo

            return ConfigAnalisesInfo.carregar_de_arquivo()
        except (OSError, ValueError, TypeError):
            return None

    @classmethod
    def resolver_estrategia(
        cls,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> EstrategiaVisualizacao:
        """Resolve a estratégia apropriada através da fábrica conforme o YAML."""
        cfg = config_analises or cls._obter_config_analises_padrao()
        engine = cfg.engine if cfg is not None else "plotly"
        return FabricaVisualizacoes.criar_estrategia(engine)

    @classmethod
    def gerar_grafico_pca_2d(
        cls,
        matriz_treino: np.ndarray | pd.DataFrame,
        rotulos: list[int],
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
        """Gera gráfico de dispersão 2D via PCA delegando para a estratégia configurada."""
        cfg = config_analises or cls._obter_config_analises_padrao()
        est = cls.resolver_estrategia(cfg)
        resultado = est.gerar_grafico_pca_2d(matriz_treino, rotulos, titulo, cfg)
        return resultado if isinstance(resultado, go.Figure) else go.Figure()

    @classmethod
    def gerar_grafico_distribuicao_clusters(
        cls,
        rotulos: list[int],
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
        """Gera gráfico de distribuição por cluster delegando para a estratégia configurada."""
        cfg = config_analises or cls._obter_config_analises_padrao()
        est = cls.resolver_estrategia(cfg)
        resultado = est.gerar_grafico_distribuicao_clusters(rotulos, titulo, cfg)
        return resultado if isinstance(resultado, go.Figure) else go.Figure()

    @classmethod
    def gerar_boxplot_atributos(
        cls,
        dados: pd.DataFrame,
        atributo: str | None = None,
        rotulos: list[int] | None = None,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
        """Gera diagramas boxplot delegando para a estratégia configurada."""
        cfg = config_analises or cls._obter_config_analises_padrao()
        est = cls.resolver_estrategia(cfg)
        resultado = est.gerar_boxplot_atributos(dados, atributo, rotulos, titulo, cfg)
        return resultado if isinstance(resultado, go.Figure) else go.Figure()

    @classmethod
    def gerar_grafico_dispersao_2_atributos(
        cls,
        dados: pd.DataFrame,
        atributo_x: str | None = None,
        atributo_y: str | None = None,
        rotulos: list[int] | None = None,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
        """Gera gráfico de dispersão 2D delegando para a estratégia configurada."""
        cfg = config_analises or cls._obter_config_analises_padrao()
        est = cls.resolver_estrategia(cfg)
        resultado = est.gerar_grafico_dispersao_2_atributos(
            dados, atributo_x, atributo_y, rotulos, titulo, cfg
        )
        return resultado if isinstance(resultado, go.Figure) else go.Figure()

    @classmethod
    def gerar_grafico_perfil_clusters(
        cls,
        resumo: ResumoAnaliseClusters,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
        """Gera perfil multivariado delegando para a estratégia configurada."""
        cfg = config_analises or cls._obter_config_analises_padrao()
        est = cls.resolver_estrategia(cfg)
        resultado = est.gerar_grafico_perfil_clusters(resumo, titulo, cfg)
        return resultado if isinstance(resultado, go.Figure) else go.Figure()

    @classmethod
    def gerar_tabela_resumo_clusters(
        cls,
        resumo: ResumoAnaliseClusters,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
        """Gera tabela consolidada de clusters delegando para a estratégia configurada."""
        cfg = config_analises or cls._obter_config_analises_padrao()
        est = cls.resolver_estrategia(cfg)
        resultado = est.gerar_tabela_resumo_clusters(resumo, titulo, cfg)
        return resultado if isinstance(resultado, go.Figure) else go.Figure()

    @classmethod
    def exportar_relatorio_html(
        cls,
        figuras: list[go.Figure | object],
        caminho_saida: str | Path,
        titulo: str | None = None,
        subtitulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> None:
        """Exporta relatório HTML delegando para a estratégia configurada."""
        cfg = config_analises or cls._obter_config_analises_padrao()
        est = cls.resolver_estrategia(cfg)
        est.exportar_relatorio_html(figuras, caminho_saida, titulo, subtitulo, cfg)
