"""Compilador de relatórios executivos em HTML e Markdown com sumários analíticos."""

from collections.abc import Mapping
from typing import final

import numpy as np
import pandas as pd

from app.avaliacao_modelos.metricas_estatisticas import ResultadoAvaliacao


def _extrair_array_float(serie: object) -> np.ndarray:
    """Extrai array unidimensional de floats finitos ignorando NaNs."""
    if not isinstance(serie, pd.Series):
        return np.empty(0, dtype=np.float64)
    arr_puro = np.asarray(serie.to_numpy(), dtype=np.float64)
    return arr_puro[np.isfinite(arr_puro)]


@final
class PainelExecutivo:
    """Consolida métricas estatísticas, rótulos de negócio e tabelas em relatório executivo."""

    def compilar_relatorio_markdown(
        self,
        metricas: ResultadoAvaliacao,
        nome_algoritmo: str,
        mapa_rotulos_negocio: Mapping[int, str] | None = None,
        dados_gold: pd.DataFrame | None = None,
    ) -> str:
        """Produz relatório textual formatado em Markdown para documentação e handoff."""
        linhas: list[str] = [
            f"# Relatório Executivo de Agrupamento — Algoritmo: {nome_algoritmo.upper()}",
            "",
            "## 1. Métricas Estatísticas Globais",
            "",
            f"- **Total de Avaliações Avaliadas:** {metricas.total_amostras}",
            f"- **Quantidade de Clusters Válidos:** {metricas.total_clusters}",
            f"- **Proporção de Ruído:** {metricas.proporcao_ruido:.2%}",
            f"- **Silhueta Global:** {metricas.silhouette_global:.4f}"
            if metricas.silhouette_global is not None
            else "- **Silhueta Global:** N/A",
            f"- **Silhueta (Sem Ruído):** {metricas.silhouette_sem_ruido:.4f}"
            if metricas.silhouette_sem_ruido is not None
            else "- **Silhueta (Sem Ruído):** N/A",
            f"- **Davies-Bouldin Index:** {metricas.davies_bouldin:.4f}"
            if metricas.davies_bouldin is not None
            else "- **Davies-Bouldin Index:** N/A",
            f"- **Calinski-Harabasz Index:** {metricas.calinski_harabasz:.2f}"
            if metricas.calinski_harabasz is not None
            else "- **Calinski-Harabasz Index:** N/A",
            "",
            "## 2. Distribuição e Rótulos de Negócio por Cluster",
            "",
            "| Cluster ID | Volumetria | Proporção | Rótulo Semântico de Negócio |",
            "|---|---|---|---|",
        ]

        rotulos = mapa_rotulos_negocio or {}
        total = float(metricas.total_amostras) if metricas.total_amostras > 0 else 1.0

        for c_id, qtd in sorted(metricas.tamanhos_clusters.items(), key=lambda x: x[0]):
            prop = (float(qtd) / total) * 100.0
            nome_negocio = rotulos.get(c_id, "padrao_nao_classificado")
            linhas.append(f"| {c_id} | {qtd} | {prop:.1f}% | {nome_negocio} |")

        if (
            dados_gold is not None
            and not dados_gold.empty
            and "horas_jogadas_total" in dados_gold.columns
        ):
            linhas.extend(
                [
                    "",
                    "## 3. Perfil de Consumo (Medianas por Cluster)",
                    "",
                    "| Cluster ID | Mediana Horas Jogadas | % Reviews Positivas |",
                    "|---|---|---|",
                ]
            )
            for c_id in sorted(metricas.tamanhos_clusters.keys()):
                sub = pd.DataFrame(dados_gold.loc[dados_gold["cluster_id"] == c_id])
                arr_horas = _extrair_array_float(sub["horas_jogadas_total"])
                horas = float(np.median(arr_horas)) if len(arr_horas) > 0 else 0.0

                if "voted_up" in sub.columns and len(sub) > 0:
                    arr_voto = np.asarray(sub["voted_up"].to_numpy(), dtype=np.bool_)
                    pos = float(np.sum(arr_voto)) / float(len(arr_voto)) * 100.0
                else:
                    pos = 0.0

                linhas.append(f"| {c_id} | {horas:.1f}h | {pos:.1f}% |")

        return "\n".join(linhas)

    def compilar_relatorio_html(
        self,
        relatorio_markdown: str,
        graficos_json: Mapping[str, str] | None = None,
    ) -> str:
        """Gera arquivo HTML completo com suporte a renderização de gráficos Plotly."""
        graficos = graficos_json or {}
        divs_graficos: list[str] = []

        for nome, json_str in graficos.items():
            div_id = f"grafico_{nome.replace(' ', '_').lower()}"
            divs_graficos.append(
                f"""
                <div class="grafico-container">
                    <h3>{nome}</h3>
                    <div id="{div_id}"></div>
                    <script>
                        var figura = {json_str};
                        Plotly.newPlot('{div_id}', figura.data, figura.layout);
                    </script>
                </div>
                """
            )

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Painel Executivo — Steam Reviews Clustering</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 30px; background-color: #f8fafc; color: #1e293b; }}
        .painel {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 25px; }}
        th, td {{ border: 1px solid #cbd5e1; padding: 10px; text-align: left; }}
        th {{ background-color: #f1f5f9; }}
        .grafico-container {{ margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 20px; }}
        pre {{ background: #f1f5f9; padding: 15px; border-radius: 6px; }}
    </style>
</head>
<body>
    <div class="painel">
        <pre>{relatorio_markdown}</pre>
        {"".join(divs_graficos)}
    </div>
</body>
</html>
"""
        return html
