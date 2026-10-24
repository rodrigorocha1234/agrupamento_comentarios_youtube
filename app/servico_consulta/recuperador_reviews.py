"""Serviço analítico para recuperação de reviews brutas por cluster para inspeção humana."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final

import pandas as pd


@dataclass(frozen=True, slots=True)
class AmostraReviewCluster:
    """Representação textual preservada de uma avaliação para auditoria humana direta."""

    recommendationid: str
    cluster_id: int
    rotulo_negocio: str
    review_texto: str
    horas_jogadas_total: float
    voted_up: bool
    votes_up: int


@final
class RecuperadorReviews:
    """Permite inspecionar amostras reais de reviews agrupadas sem executar PLN."""

    def recuperar_amostras_cluster(
        self,
        dados_gold: pd.DataFrame,
        cluster_id: int,
        quantidade: int = 10,
        random_state: int = 42,
    ) -> Sequence[AmostraReviewCluster]:
        """Extrai amostras aleatórias de avaliações pertencentes a um cluster específico."""
        if "cluster_id" not in dados_gold.columns or dados_gold.empty:
            return []

        sub_cluster = dados_gold[dados_gold["cluster_id"] == cluster_id]
        if sub_cluster.empty:
            return []

        # Amostragem determinística
        n_amostras = min(quantidade, len(sub_cluster))
        amostra_df = sub_cluster.sample(n=n_amostras, random_state=random_state)

        amostras: list[AmostraReviewCluster] = []
        for _, linha in amostra_df.iterrows():
            amostras.append(
                AmostraReviewCluster(
                    recommendationid=str(linha.get("recommendationid", "")),
                    cluster_id=cluster_id,
                    rotulo_negocio=str(linha.get("rotulo_negocio", "sem_rotulo")),
                    review_texto=str(linha.get("review_texto", "")),
                    horas_jogadas_total=float(
                        linha.get("horas_jogadas_total", 0.0) or 0.0
                    ),
                    voted_up=bool(linha.get("voted_up", False)),
                    votes_up=int(linha.get("votes_up", 0) or 0),
                )
            )

        return amostras

    def recuperar_todas_por_cluster(
        self,
        dados_gold: pd.DataFrame,
        quantidade_por_cluster: int = 5,
        random_state: int = 42,
    ) -> dict[int, Sequence[AmostraReviewCluster]]:
        """Gera um mapa estruturado com amostras de cada cluster presente no conjunto."""
        if "cluster_id" not in dados_gold.columns:
            return {}

        clusters = sorted(dados_gold["cluster_id"].unique())
        resultado: dict[int, Sequence[AmostraReviewCluster]] = {}

        for c_id in clusters:
            resultado[int(c_id)] = self.recuperar_amostras_cluster(
                dados_gold=dados_gold,
                cluster_id=int(c_id),
                quantidade=quantidade_por_cluster,
                random_state=random_state,
            )

        return resultado
