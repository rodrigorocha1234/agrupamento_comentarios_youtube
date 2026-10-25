"""Rastreador de evolução temporal e drift de distribuição de clusters Steam."""

from collections.abc import Sequence
from typing import final

import numpy as np
import pandas as pd

from app.dominio_contratos.modelos_dados import TipoValorEscalar


def _extrair_array_float(serie: pd.Series | pd.DataFrame | Sequence[float] | None) -> np.ndarray:
    """Extrai array unidimensional de floats finitos ignorando NaNs com segurança de tipos."""
    if not isinstance(serie, pd.Series):
        return np.empty(0, dtype=np.float64)
    arr_puro = np.asarray(serie.to_numpy(), dtype=np.float64)
    return arr_puro[np.isfinite(arr_puro)]


@final
class RastreadorEvolucaoTemporal:

    """Calcula indicadores agregados de estabilidade, migração e evolução temporal."""

    def calcular_evolucao_temporal(
        self,
        dados: pd.DataFrame,
        coluna_timestamp: str = "timestamp_created",
        coluna_cluster: str = "cluster_id",
        coluna_voto: str = "voted_up",
        coluna_horas: str = "playtime_forever",
    ) -> pd.DataFrame:
        """Gera painel temporal sumarizado por janela mensal e identificador de cluster."""
        if dados.empty:
            return pd.DataFrame()

        df_trabalho = dados.copy()

        # Criação da janela temporal 'ano_mes'
        if coluna_timestamp in df_trabalho.columns:
            # Converte timestamps Unix ou strings ISO
            serie_ts = pd.to_datetime(
                df_trabalho[coluna_timestamp], unit="s", errors="coerce"
            )
            if serie_ts.isna().all():
                serie_ts = pd.to_datetime(
                    df_trabalho[coluna_timestamp], errors="coerce"
                )
            df_trabalho["ano_mes"] = serie_ts.dt.to_period("M").astype(str)
        else:
            df_trabalho["ano_mes"] = "indefinido"

        if coluna_cluster not in df_trabalho.columns:
            df_trabalho[coluna_cluster] = 0

        # Agregação temporal
        linhas_resumo: list[dict[str, TipoValorEscalar]] = []
        janelas_unicas = sorted(df_trabalho["ano_mes"].unique())

        for janela in janelas_unicas:
            df_janela = pd.DataFrame(df_trabalho.loc[df_trabalho["ano_mes"] == janela])
            total_janela = len(df_janela)
            if total_janela == 0:
                continue

            clusters_janela = list(df_janela[coluna_cluster].unique())
            for c_id in clusters_janela:
                df_sub = pd.DataFrame(df_janela.loc[df_janela[coluna_cluster] == c_id])
                qtd = len(df_sub)
                prop = (qtd / total_janela) * 100.0


                # Taxa de votos positivos
                taxa_positivas = 0.0
                if coluna_voto in df_sub.columns:
                    votos = np.asarray(df_sub[coluna_voto].to_numpy(), dtype=np.bool_)
                    if len(votos) > 0:
                        taxa_positivas = float(np.mean(votos)) * 100.0

                # Mediana de horas
                mediana_horas = 0.0
                if coluna_horas in df_sub.columns:
                    arr_horas = _extrair_array_float(df_sub[coluna_horas])
                    if len(arr_horas) > 0:
                        mediana_horas = float(np.median(arr_horas))


                linhas_resumo.append(
                    {
                        "ano_mes": str(janela),
                        "cluster_id": int(str(c_id)),
                        "total_reviews": int(qtd),
                        "proporcao_janela_percentual": float(round(prop, 2)),
                        "taxa_reviews_positivas": float(round(taxa_positivas, 2)),
                        "mediana_horas_jogadas": float(round(mediana_horas, 2)),
                    }
                )

        return pd.DataFrame(linhas_resumo)
