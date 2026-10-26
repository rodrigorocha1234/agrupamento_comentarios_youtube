"""Implementação alternativa (GoF Concrete Strategy) para gráficos Altair / Vega-Lite."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from app.analise_clusters.analisador_clusters import ResumoAnaliseClusters
from app.analise_clusters.estrategia_visualizacao import (
    EstrategiaVisualizacao,
    FiguraAnalitica,
)
from app.analise_temporal.contratos import ResumoAnaliseTemporal
from app.contratos.tipos_dados import DicionarioJson

if TYPE_CHECKING:
    from app.conf_yaml import ConfigAnalisesInfo


class EstrategiaVisualizacaoAltair(EstrategiaVisualizacao):
    """Implementação alternativa (GoF Concrete Strategy) para gráficos Altair / Vega-Lite."""

    def gerar_grafico_pca_2d(
        self,
        matriz_treino: np.ndarray | pd.DataFrame,
        rotulos: list[int],
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> DicionarioJson:
        cfg = config_analises
        titulo_final = (
            titulo
            or (cfg.layout.titulo_pca if cfg is not None else "Projeção Exploratória dos Agrupamentos (PCA 2D)")
        )
        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": titulo_final,
            "mark": "circle",
            "encoding": {
                "x": {"field": "comp_1", "type": "quantitative"},
                "y": {"field": "comp_2", "type": "quantitative"},
                "color": {"field": "cluster", "type": "nominal"},
            },
        }

    def gerar_grafico_distribuicao_clusters(
        self,
        rotulos: list[int],
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> DicionarioJson:
        cfg = config_analises
        titulo_final = (
            titulo
            or (
                cfg.layout.titulo_distribuicao
                if cfg is not None
                else "Distribuição de Amostras por Cluster"
            )
        )
        eixo_x = cfg.layout.eixo_x_distribuicao if cfg is not None else "Agrupamento"
        eixo_y = cfg.layout.eixo_y_distribuicao if cfg is not None else "Quantidade de Amostras"
        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": titulo_final,
            "mark": "bar",
            "encoding": {
                "x": {"field": "cluster", "type": "nominal", "title": eixo_x},
                "y": {"field": "quantidade", "type": "quantitative", "title": eixo_y},
            },
        }

    def gerar_boxplot_atributos(
        self,
        dados: pd.DataFrame,
        atributo: str | None = None,
        rotulos: list[int] | None = None,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> DicionarioJson:
        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": titulo or f"Distribuição de '{atributo}' por Cluster",
            "mark": "boxplot",
        }

    def gerar_grafico_dispersao_2_atributos(
        self,
        dados: pd.DataFrame,
        atributo_x: str | None = None,
        atributo_y: str | None = None,
        rotulos: list[int] | None = None,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> DicionarioJson:
        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": titulo or f"Dispersão: {atributo_x} vs {atributo_y}",
            "mark": "point",
        }

    def gerar_grafico_perfil_clusters(
        self,
        resumo: ResumoAnaliseClusters,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> DicionarioJson:
        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": titulo or "Perfil Médio dos Atributos por Cluster",
            "mark": "bar",
        }

    def gerar_tabela_resumo_clusters(
        self,
        resumo: ResumoAnaliseClusters,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> DicionarioJson:
        return {
            "tipo": "tabela_resumo_altair",
            "titulo": titulo or "Resumo Estatístico dos Clusters",
            "perfis": len(resumo.perfis),
        }

    def gerar_grafico_evolucao_temporal(
        self,
        resumo_temporal: ResumoAnaliseTemporal,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> DicionarioJson:
        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": titulo or "Evolução Histórica do Volume por Agrupamento (Altair)",
            "mark": "line",
            "encoding": {
                "x": {"field": "periodo", "type": "ordinal"},
                "y": {"field": "quantidade", "type": "quantitative"},
                "color": {"field": "cluster", "type": "nominal"},
            },
        }

    def gerar_grafico_area_empilhada_temporal(
        self,
        resumo_temporal: ResumoAnaliseTemporal,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> DicionarioJson:
        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": titulo or "Composição Relativa dos Agrupamentos (Altair)",
            "mark": "area",
            "encoding": {
                "x": {"field": "periodo", "type": "ordinal"},
                "y": {"field": "proporcao", "type": "quantitative", "stack": "normalize"},
                "color": {"field": "cluster", "type": "nominal"},
            },
        }

    def exportar_relatorio_html(
        self,
        figuras: list[FiguraAnalitica],
        caminho_saida: str | Path,
        titulo: str | None = None,
        subtitulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> None:
        caminho = Path(caminho_saida)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        specs_json = [json.dumps(fig) if isinstance(fig, dict) else str(fig) for fig in figuras]
        blocos = [
            "<!DOCTYPE html><html><head><meta charset='utf-8'/>",
            f"<title>{titulo or 'Relatório Analítico Altair'}</title>",
            "<script src='https://cdn.jsdelivr.net/npm/vega@5'></script>",
            "<script src='https://cdn.jsdelivr.net/npm/vega-lite@5'></script>",
            "<script src='https://cdn.jsdelivr.net/npm/vega-embed@6'></script>",
            "</head><body>",
            f"<h1>{titulo or 'Relatório Analítico Altair'}</h1>",
            f"<p>{subtitulo or ''}</p>",
        ]
        for idx, spec in enumerate(specs_json):
            div_id = f"vis_{idx}"
            blocos.append(f"<div id='{div_id}'></div>")
            blocos.append(f"<script>vegaEmbed('#{div_id}', {spec});</script>")
        blocos.append("</body></html>")
        caminho.write_text("\n".join(blocos), encoding="utf-8")
