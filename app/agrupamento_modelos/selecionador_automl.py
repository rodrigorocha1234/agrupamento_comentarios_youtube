"""Seleção automatizada de modelos (AutoML) para clustering guiada por capacidades."""

from collections.abc import Mapping, Sequence
from typing import final

import numpy as np

from app.agrupamento_modelos.capacidades_algoritmo import EstrategiaAgrupamento
from app.agrupamento_modelos.fabrica_agrupadores import FabricaAgrupadores
from app.avaliacao_modelos.avaliador_clusters import AvaliadorClusters
from app.avaliacao_modelos.metricas_estatisticas import ResultadoAvaliacao
from app.dominio_contratos.modelos_dados import TipoParametroAlgoritmo
from app.otimizacao_hiperparametros.avaliador_objetivo import AvaliadorObjetivo


@final
class SelecionadorModelosAutoML:
    """Avalia múltiplos algoritmos e parametrizações para eleger o modelo campeão."""

    def __init__(
        self,
        fabrica: FabricaAgrupadores | None = None,
        avaliador: AvaliadorClusters | None = None,
        avaliador_objetivo: AvaliadorObjetivo | None = None,
    ) -> None:
        self._fabrica = fabrica or FabricaAgrupadores()
        self._avaliador = avaliador or AvaliadorClusters()
        self._avaliador_objetivo = avaliador_objetivo or AvaliadorObjetivo()

    def selecionar_melhor_modelo(
        self,
        matriz_x: np.ndarray,
        candidatos: Sequence[tuple[str, Mapping[str, TipoParametroAlgoritmo]]] | None = None,
    ) -> tuple[EstrategiaAgrupamento, ResultadoAvaliacao, str, float]:
        """Treina e pontua todos os candidatos, retornando o modelo ótimo e suas métricas."""
        lista_candidatos: list[tuple[str, Mapping[str, TipoParametroAlgoritmo]]] = list(
            candidatos
            or [
                ("kmeans", {"n_clusters": 2, "n_init": 10}),
                ("kmeans", {"n_clusters": 3, "n_init": 10}),
                ("dbscan", {"eps": 1.5, "min_samples": 5}),
                ("hdbscan", {"min_cluster_size": 5}),
            ]
        )

        melhor_modelo: EstrategiaAgrupamento | None = None
        melhor_avaliacao: ResultadoAvaliacao | None = None
        melhor_algoritmo = ""
        melhor_score = -999.0

        for nome_algoritmo, params in lista_candidatos:
            try:
                estimador = self._fabrica.criar_agrupador(nome_algoritmo, dict(params))

                rotulos = estimador.treinar(matriz_x)
                avaliacao = self._avaliador.avaliar(matriz_x, rotulos)
                resultado_obj = self._avaliador_objetivo.calcular_score(avaliacao)
                score = resultado_obj.score_composto

                if resultado_obj.valido and score > melhor_score:
                    melhor_score = score
                    melhor_modelo = estimador
                    melhor_avaliacao = avaliacao
                    melhor_algoritmo = nome_algoritmo
            except (ValueError, TypeError, RuntimeError):
                continue

        if melhor_modelo is None or melhor_avaliacao is None:
            # Fallback seguro para KMeans padrão se nenhum convergir
            fallback = self._fabrica.criar_agrupador("kmeans", {"n_clusters": 2})
            rotulos = fallback.treinar(matriz_x)
            avaliacao = self._avaliador.avaliar(matriz_x, rotulos)
            return fallback, avaliacao, "kmeans", -1.0

        return melhor_modelo, melhor_avaliacao, melhor_algoritmo, melhor_score
