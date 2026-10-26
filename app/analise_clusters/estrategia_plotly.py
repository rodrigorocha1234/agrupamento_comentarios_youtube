"""Implementação concreta (GoF Concrete Strategy) para visualizações com Plotly."""

from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.decomposition import PCA

from app.analise_clusters.analisador_clusters import ResumoAnaliseClusters
from app.analise_clusters.estrategia_visualizacao import (
    AVISO_PCA,
    EstrategiaVisualizacao,
    FiguraAnalitica,
)
from app.analise_temporal.contratos import ResumoAnaliseTemporal

if TYPE_CHECKING:
    from app.conf_yaml import ConfigAnalisesInfo


class EstrategiaVisualizacaoPlotly(EstrategiaVisualizacao):
    """Implementação concreta (GoF Concrete Strategy) utilizando a biblioteca Plotly."""

    def gerar_grafico_pca_2d(
        self,
        matriz_treino: np.ndarray | pd.DataFrame,
        rotulos: list[int],
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
        cfg = config_analises
        titulo_final = (
            titulo
            or (cfg.layout.titulo_pca if cfg is not None else "Projeção Exploratória dos Agrupamentos (PCA 2D)")
        )
        tema = cfg.layout.tema if cfg is not None else "plotly_white"
        cor_ruido = cfg.layout.cor_ruido if cfg is not None else "#888888"
        rotulo_ruido = cfg.layout.rotulo_ruido if cfg is not None else "Ruído (-1)"

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
            nome = rotulo_ruido if r == -1 else f"Cluster {r}"
            cor = cor_ruido if r == -1 else None

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
            title=titulo_final,
            xaxis_title="Componente Principal 1",
            yaxis_title="Componente Principal 2",
            template=tema,
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

    def gerar_grafico_distribuicao_clusters(
        self,
        rotulos: list[int],
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
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
        tema = cfg.layout.tema if cfg is not None else "plotly_white"
        cor_ruido = cfg.layout.cor_ruido if cfg is not None else "#e74c3c"
        cor_padrao = cfg.layout.cor_cluster_padrao if cfg is not None else "#3498db"
        rotulo_ruido = cfg.layout.rotulo_ruido if cfg is not None else "Ruído (-1)"

        contagem = Counter(rotulos)
        total = len(rotulos) if rotulos else 1

        clusters = sorted(contagem.keys())
        nomes = [rotulo_ruido if c == -1 else f"Cluster {c}" for c in clusters]
        valores = [contagem[c] for c in clusters]
        percentuais = [f"{(v / total) * 100:.1f}%" for v in valores]
        cores = [cor_ruido if c == -1 else cor_padrao for c in clusters]

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
            title=titulo_final,
            xaxis_title=eixo_x,
            yaxis_title=eixo_y,
            template=tema,
        )
        return fig

    def gerar_boxplot_atributos(
        self,
        dados: pd.DataFrame,
        atributo: str | None = None,
        rotulos: list[int] | None = None,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
        if rotulos is None or len(dados) != len(rotulos):
            return go.Figure()

        cfg = config_analises
        atributo_alvo = atributo
        if atributo_alvo is None:
            if cfg is not None and cfg.boxplot.atributo and cfg.boxplot.atributo in dados.columns:
                atributo_alvo = cfg.boxplot.atributo
            elif len(dados.columns) > 0:
                atributo_alvo = str(dados.columns[0])
            else:
                return go.Figure()

        if atributo_alvo not in dados.columns:
            return go.Figure()

        rotulo_ruido = cfg.layout.rotulo_ruido if cfg is not None else "Ruído (-1)"
        tema = cfg.layout.tema if cfg is not None else "plotly_white"

        df_aux = pd.DataFrame(
            {
                "valor": dados[atributo_alvo].to_numpy(dtype=np.float64),
                "cluster": [rotulo_ruido if r == -1 else f"Cluster {r}" for r in rotulos],
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

        titulo_final = titulo or f"Distribuição de '{atributo_alvo}' por Cluster"
        fig.update_layout(
            title=titulo_final,
            yaxis_title=atributo_alvo,
            xaxis_title="Cluster",
            template=tema,
        )
        return fig

    def gerar_grafico_dispersao_2_atributos(
        self,
        dados: pd.DataFrame,
        atributo_x: str | None = None,
        atributo_y: str | None = None,
        rotulos: list[int] | None = None,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
        fig = go.Figure()
        if rotulos is None or len(dados) != len(rotulos):
            return fig

        cfg = config_analises
        alvo_x = atributo_x
        alvo_y = atributo_y

        if alvo_x is None:
            if cfg is not None and cfg.dispersao.atributo_x and cfg.dispersao.atributo_x in dados.columns:
                alvo_x = cfg.dispersao.atributo_x
            elif len(dados.columns) >= 1:
                alvo_x = str(dados.columns[0])

        if alvo_y is None:
            if cfg is not None and cfg.dispersao.atributo_y and cfg.dispersao.atributo_y in dados.columns:
                alvo_y = cfg.dispersao.atributo_y
            elif len(dados.columns) >= 2:
                alvo_y = str(dados.columns[1])

        if alvo_x is None or alvo_y is None or alvo_x not in dados.columns or alvo_y not in dados.columns:
            return fig

        tema = cfg.layout.tema if cfg is not None else "plotly_white"
        cor_ruido = cfg.layout.cor_ruido if cfg is not None else "#888888"
        rotulo_ruido = cfg.layout.rotulo_ruido if cfg is not None else "Ruído (-1)"

        rotulos_unicos = sorted(set(rotulos))
        x_vals = np.asarray(dados[alvo_x].to_numpy(dtype=np.float64), dtype=np.float64)
        y_vals = np.asarray(dados[alvo_y].to_numpy(dtype=np.float64), dtype=np.float64)

        for r in rotulos_unicos:
            idx = [i for i, val in enumerate(rotulos) if val == r]
            nome = rotulo_ruido if r == -1 else f"Cluster {r}"
            cor = cor_ruido if r == -1 else None

            fig.add_trace(
                go.Scatter(
                    x=x_vals[idx],
                    y=y_vals[idx],
                    mode="markers",
                    name=nome,
                    marker={"size": 7, "opacity": 0.8, "color": cor},
                    text=[f"Amostra {i} | {nome}" for i in idx],
                    hoverinfo="text+x+y",
                )
            )

        titulo_final = titulo or f"Dispersão de Clusters: {alvo_x} vs {alvo_y}"
        fig.update_layout(
            title=titulo_final,
            xaxis_title=alvo_x,
            yaxis_title=alvo_y,
            template=tema,
        )
        return fig

    def gerar_grafico_perfil_clusters(
        self,
        resumo: ResumoAnaliseClusters,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
        fig = go.Figure()
        if not resumo.perfis:
            return fig

        cfg = config_analises
        titulo_final = (
            titulo
            or (cfg.layout.titulo_perfil if cfg is not None else "Perfil Médio dos Atributos por Cluster")
        )
        tema = cfg.layout.tema if cfg is not None else "plotly_white"
        rotulo_ruido = cfg.layout.rotulo_ruido if cfg is not None else "Ruído (-1)"

        atributos = resumo.atributos_analisados
        if not atributos:
            atributos = list(resumo.perfis[0].medias_atributos.keys())

        if not atributos:
            return fig

        for perfil in resumo.perfis:
            if perfil.id_cluster == -1:
                nome = rotulo_ruido
            else:
                persona = f" ({perfil.rotulo_negocio})" if perfil.rotulo_negocio else ""
                nome = f"Cluster {perfil.id_cluster}{persona}"

            valores_medias = [perfil.medias_atributos.get(attr, 0.0) for attr in atributos]

            fig.add_trace(
                go.Bar(
                    name=nome,
                    x=atributos,
                    y=valores_medias,
                )
            )

        fig.update_layout(
            title=titulo_final,
            xaxis_title="Atributos Analisados",
            yaxis_title="Valor Médio",
            barmode="group",
            template=tema,
        )
        return fig

    def gerar_tabela_resumo_clusters(
        self,
        resumo: ResumoAnaliseClusters,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
        cfg = config_analises
        titulo_final = (
            titulo or (cfg.layout.titulo_resumo if cfg is not None else "Resumo Estatístico dos Clusters")
        )
        rotulo_ruido = cfg.layout.rotulo_ruido if cfg is not None else "Ruído (-1)"
        tema = cfg.layout.tema if cfg is not None else "plotly_white"

        col_cluster = cfg.tabela_resumo.coluna_cluster if cfg is not None else "Cluster"
        col_persona = cfg.tabela_resumo.coluna_persona if cfg is not None else "Persona / Negócio"
        col_alerta = cfg.tabela_resumo.coluna_alerta if cfg is not None else "Alerta"
        col_qtd = cfg.tabela_resumo.coluna_quantidade if cfg is not None else "Qtd Amostras"
        col_prop = cfg.tabela_resumo.coluna_proporcao if cfg is not None else "Proporção (%)"
        col_dist = cfg.tabela_resumo.coluna_distancia_centroide if cfg is not None else "Dist. Centroide"

        chaves_metricas: list[str] = []
        for p in resumo.perfis:
            for k in p.metricas_personalizadas:
                if k not in chaves_metricas:
                    chaves_metricas.append(k)

        headers: list[str] = [
            col_cluster,
            col_persona,
            col_alerta,
            col_qtd,
            col_prop,
        ]
        for metrica in chaves_metricas:
            headers.append(metrica.replace("_", " ").title())
        headers.append(col_dist)

        linhas_id: list[str] = []
        linhas_rotulo: list[str] = []
        linhas_alerta: list[str] = []
        linhas_qtd: list[int] = []
        linhas_prop: list[str] = []
        linhas_metricas: dict[str, list[str]] = {k: [] for k in chaves_metricas}
        linhas_dist: list[str] = []

        for p in resumo.perfis:
            linhas_id.append(rotulo_ruido if p.id_cluster == -1 else f"Cluster {p.id_cluster}")
            linhas_rotulo.append(p.rotulo_negocio or "-")
            linhas_alerta.append("SIM" if p.alerta_negocio else "Não")
            linhas_qtd.append(p.quantidade_amostras)
            linhas_prop.append(f"{p.proporcao_amostras * 100:.1f}%")

            for k in chaves_metricas:
                val = p.metricas_personalizadas.get(k)
                if val is None:
                    linhas_metricas[k].append("-")
                elif "taxa" in k.lower() or "proporcao" in k.lower() or "porcentagem" in k.lower():
                    linhas_metricas[k].append(f"{val * 100:.1f}%")
                else:
                    linhas_metricas[k].append(f"{val:.2f}")

            linhas_dist.append(
                f"{p.distancia_media_centroide:.3f}" if p.distancia_media_centroide is not None else "-"
            )

        colunas_tabela: list[list[str] | list[int]] = [
            linhas_id,
            linhas_rotulo,
            linhas_alerta,
            linhas_qtd,
            linhas_prop,
        ]
        for k in chaves_metricas:
            colunas_tabela.append(linhas_metricas[k])
        colunas_tabela.append(linhas_dist)

        fig = go.Figure(
            data=[
                go.Table(
                    header={
                        "values": headers,
                        "fill_color": "#2c3e50",
                        "align": "center",
                        "font": {"color": "white", "size": 12},
                    },
                    cells={
                        "values": colunas_tabela,
                        "fill_color": "#f8f9fa",
                        "align": "center",
                        "font": {"size": 11},
                        "height": 28,
                    },
                )
            ]
        )

        fig.update_layout(title=titulo_final, template=tema)
        return fig

    def gerar_grafico_evolucao_temporal(
        self,
        resumo_temporal: ResumoAnaliseTemporal,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
        """Gera série temporal com o volume cronológico por cluster e marcação de anomalias/picos."""
        cfg = config_analises
        titulo_final = titulo or "Evolução Histórica do Volume por Agrupamento"
        tema = cfg.layout.tema if cfg is not None else "plotly_white"
        cor_ruido = cfg.layout.cor_ruido if cfg is not None else "#888888"

        fig = go.Figure()
        periodos = resumo_temporal.periodos_ordenados
        clusters = resumo_temporal.clusters_presentes

        for cid in clusters:
            pontos_cid = [p for p in resumo_temporal.pontos_temporais if p.id_cluster == cid]
            mapa_qtd = {p.periodo: p.quantidade_amostras for p in pontos_cid}
            y_valores = [mapa_qtd.get(per, 0) for per in periodos]
            nome_rotulo = pontos_cid[0].nome_rotulo if pontos_cid else f"Cluster {cid}"

            linha_cor = cor_ruido if cid == -1 else None

            fig.add_trace(
                go.Scatter(
                    x=periodos,
                    y=y_valores,
                    mode="lines+markers",
                    name=nome_rotulo,
                    line={"color": linha_cor} if linha_cor else None,
                )
            )

        # Destaca anomalias/picos identificados
        for alerta in resumo_temporal.alertas_picos:
            fig.add_annotation(
                x=alerta.periodo,
                y=alerta.valor_observado,
                text=f"Pico {alerta.nome_rotulo} (+{alerta.z_score:.1f}σ)",
                showarrow=True,
                arrowhead=2,
                arrowcolor="#e74c3c",
                bgcolor="#fadbd8",
                bordercolor="#e74c3c",
                font={"size": 10, "color": "#78281f"},
            )

        fig.update_layout(
            title={"text": titulo_final, "x": 0.5, "xanchor": "center"},
            template=tema,
            xaxis_title="Período Cronológico",
            yaxis_title="Quantidade de Avaliações",
            hovermode="x unified",
        )
        return fig

    def gerar_grafico_area_empilhada_temporal(
        self,
        resumo_temporal: ResumoAnaliseTemporal,
        titulo: str | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> go.Figure:
        """Gera gráfico de área 100% empilhada demonstrando a dinâmica de composição dos grupos."""
        cfg = config_analises
        titulo_final = titulo or "Composição Relativa dos Agrupamentos ao Longo do Tempo"
        tema = cfg.layout.tema if cfg is not None else "plotly_white"
        cor_ruido = cfg.layout.cor_ruido if cfg is not None else "#888888"

        fig = go.Figure()
        periodos = resumo_temporal.periodos_ordenados
        clusters = resumo_temporal.clusters_presentes

        for cid in clusters:
            pontos_cid = [p for p in resumo_temporal.pontos_temporais if p.id_cluster == cid]
            mapa_prop = {p.periodo: p.proporcao_periodo * 100.0 for p in pontos_cid}
            y_valores = [mapa_prop.get(per, 0.0) for per in periodos]
            nome_rotulo = pontos_cid[0].nome_rotulo if pontos_cid else f"Cluster {cid}"

            linha_cor = cor_ruido if cid == -1 else None

            fig.add_trace(
                go.Scatter(
                    x=periodos,
                    y=y_valores,
                    mode="lines",
                    stackgroup="clusters_stack",
                    name=nome_rotulo,
                    line={"color": linha_cor} if linha_cor else None,
                )
            )

        fig.update_layout(
            title={"text": titulo_final, "x": 0.5, "xanchor": "center"},
            template=tema,
            xaxis_title="Período Cronológico",
            yaxis_title="Participação Percentual (%)",
            yaxis={"range": [0, 100]},
            hovermode="x unified",
        )
        return fig

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

        cfg = config_analises
        titulo_relatorio = (
            titulo
            or (cfg.layout.titulo_relatorio if cfg is not None else "Relatório Analítico de Agrupamento")
        )
        subtitulo_relatorio = (
            subtitulo
            or (
                cfg.layout.subtitulo_relatorio
                if cfg is not None
                else "Diagnósticos visuais, distribuição de grupos e projeções multidimensionais."
            )
        )

        blocos_html: list[str] = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'/>",
            f"<title>{titulo_relatorio}</title>",
            "<style>body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 30px; background-color: #f8f9fa; } .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }</style>",
            "</head>",
            "<body>",
            f"<h1>{titulo_relatorio}</h1>",
            f"<p>{subtitulo_relatorio}</p>",
        ]

        for i, fig in enumerate(figuras):
            if isinstance(fig, go.Figure):
                include_js = i == 0
                div_html = fig.to_html(full_html=False, include_plotlyjs="cdn" if include_js else False)
                blocos_html.append(f"<div class='card'>{div_html}</div>")
            else:
                metodo_to_html = getattr(fig, "to_html", None)
                if callable(metodo_to_html):
                    div_html = str(metodo_to_html())
                    blocos_html.append(f"<div class='card'>{div_html}</div>")
                else:
                    blocos_html.append(f"<div class='card'><pre>{fig}</pre></div>")

        blocos_html.append("</body></html>")
        caminho.write_text("\n".join(blocos_html), encoding="utf-8")
