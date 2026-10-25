"""Módulo de sumarização diagnóstica e análise de perfis de clusters."""

from dataclasses import dataclass
from typing import Final

import numpy as np
import pandas as pd

ROTULO_RUIDO: Final[str] = "Ruído / Outlier"


@dataclass(frozen=True)
class PerfilCluster:
    """Consolida as características estatísticas de um cluster específico."""

    id_cluster: int
    nome_rotulo: str
    quantidade_amostras: int
    proporcao_amostras: float
    medias_atributos: dict[str, float]
    medianas_atributos: dict[str, float]
    taxa_recomendacao: float | None = None
    media_horas_jogadas: float | None = None
    distancia_media_centroide: float | None = None


@dataclass(frozen=True)
class ResumoAnaliseClusters:
    """Relatório estruturado de perfis de todos os agrupamentos gerados."""

    perfis: list[PerfilCluster]
    total_amostras: int
    quantidade_clusters_validos: int
    quantidade_ruido: int
    proporcao_ruido: float
    atributos_analisados: list[str]


class AnalisadorClusters:
    """Calcula estatísticas descritivas, perfis agregados e isolamento de ruído."""

    @staticmethod
    def gerar_resumo_estatistico(
        matriz_treino: pd.DataFrame | np.ndarray,
        rotulos: list[int],
        metadados: pd.DataFrame | None = None,
        centroides: np.ndarray | None = None,
        nomes_colunas_matriz: list[str] | None = None,
    ) -> ResumoAnaliseClusters:
        """Produz o sumário descritivo por cluster cruzando atributos com metadados."""
        total_amostras = len(rotulos)
        if total_amostras == 0:
            return ResumoAnaliseClusters(
                perfis=[],
                total_amostras=0,
                quantidade_clusters_validos=0,
                quantidade_ruido=0,
                proporcao_ruido=0.0,
                atributos_analisados=[],
            )

        if isinstance(matriz_treino, pd.DataFrame):
            colunas_atributos = list(matriz_treino.columns)
            matriz_np = np.asarray(matriz_treino.to_numpy(dtype=np.float64), dtype=np.float64)
        else:
            matriz_np = np.asarray(matriz_treino, dtype=np.float64)
            colunas_atributos = (
                nomes_colunas_matriz
                if nomes_colunas_matriz is not None and len(nomes_colunas_matriz) == matriz_np.shape[1]
                else [f"attr_{i}" for i in range(matriz_np.shape[1])]
            )

        rotulos_unicos = sorted(set(rotulos))
        clusters_validos = [r for r in rotulos_unicos if r != -1]
        qtd_ruido = rotulos.count(-1)
        prop_ruido = float(qtd_ruido / total_amostras)

        # Distâncias aos centroides se presentes
        distancias: np.ndarray | None = None
        if centroides is not None and len(centroides) > 0 and len(clusters_validos) > 0:
            distancias = np.zeros(total_amostras, dtype=np.float64)
            for idx, r in enumerate(rotulos):
                if 0 <= r < len(centroides):
                    ponto = matriz_np[idx]
                    centro = centroides[r]
                    distancias[idx] = float(np.linalg.norm(ponto - centro))
                else:
                    distancias[idx] = np.nan

        perfis: list[PerfilCluster] = []

        for r in rotulos_unicos:
            mascara = [i for i, val in enumerate(rotulos) if val == r]
            qtd = len(mascara)
            prop = float(qtd / total_amostras)
            nome = ROTULO_RUIDO if r == -1 else f"Cluster {r}"

            subset_matriz = matriz_np[mascara]

            medias: dict[str, float] = {}
            medianas: dict[str, float] = {}
            for col_idx, nome_col in enumerate(colunas_atributos):
                medias[nome_col] = float(np.mean(subset_matriz[:, col_idx]))
                medianas[nome_col] = float(np.median(subset_matriz[:, col_idx]))

            taxa_recom: float | None = None
            media_horas: float | None = None

            if metadados is not None and not metadados.empty:
                subset_meta = metadados.iloc[mascara]
                if "voted_up" in subset_meta.columns:
                    col_voted = subset_meta["voted_up"]
                    taxa_recom = float(col_voted.astype(float).mean())

                if "author_playtime_forever" in subset_meta.columns:
                    media_minutos = float(subset_meta["author_playtime_forever"].astype(float).mean())
                    media_horas = round(media_minutos / 60.0, 2)

            dist_media: float | None = None
            if distancias is not None and r != -1:
                dist_subset = distancias[mascara]
                dist_validas = dist_subset[~np.isnan(dist_subset)]
                if len(dist_validas) > 0:
                    dist_media = float(np.mean(dist_validas))

            perfis.append(
                PerfilCluster(
                    id_cluster=r,
                    nome_rotulo=nome,
                    quantidade_amostras=qtd,
                    proporcao_amostras=prop,
                    medias_atributos=medias,
                    medianas_atributos=medianas,
                    taxa_recomendacao=taxa_recom,
                    media_horas_jogadas=media_horas,
                    distancia_media_centroide=dist_media,
                )
            )

        return ResumoAnaliseClusters(
            perfis=perfis,
            total_amostras=total_amostras,
            quantidade_clusters_validos=len(clusters_validos),
            quantidade_ruido=qtd_ruido,
            proporcao_ruido=prop_ruido,
            atributos_analisados=colunas_atributos,
        )

    @staticmethod
    def extrair_amostras_reviews_por_cluster(
        metadados: pd.DataFrame,
        rotulos: list[int],
        amostras_por_cluster: int = 5,
    ) -> dict[int, list[dict[str, str | int | float | bool]]]:
        """Extrai exemplos de reviews originais por cluster para inspeção humana."""
        if metadados.empty or len(rotulos) != len(metadados):
            return {}

        df_aux = metadados.copy()
        df_aux["_cluster_rotulo"] = rotulos

        resultado: dict[int, list[dict[str, str | int | float | bool]]] = {}
        for r in sorted(set(rotulos)):
            subset = df_aux[df_aux["_cluster_rotulo"] == r]
            amostra = subset.head(amostras_por_cluster)

            lista_registros: list[dict[str, str | int | float | bool]] = []
            for _, row in amostra.iterrows():
                registro: dict[str, str | int | float | bool] = {}
                for col in ["recommendationid", "review", "voted_up", "votes_up", "author_playtime_forever"]:
                    if col in row:
                        val = row[col]
                        if bool(pd.isna(val)):
                            registro[col] = ""
                        elif isinstance(val, (bool, int, float, str)):
                            registro[col] = val
                        else:
                            registro[col] = str(val)
                lista_registros.append(registro)

            resultado[r] = lista_registros

        return resultado
