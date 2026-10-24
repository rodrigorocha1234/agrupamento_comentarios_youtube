from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import final

import numpy as np

from app.agrupamento_modelos.capacidades_algoritmo import EstrategiaAgrupamento
from app.agrupamento_modelos.fabrica_agrupadores import FabricaAgrupadores
from app.avaliacao_modelos.avaliador_clusters import AvaliadorClusters
from app.avaliacao_modelos.metricas_estatisticas import ResultadoAvaliacao
from app.otimizacao_hiperparametros.avaliador_objetivo import (
    AvaliadorObjetivo,
    ResultadoObjetivo,
)


@dataclass(frozen=True, slots=True)
class CandidatoHiperparametros:
    """Registro de uma tentativa avaliada durante a busca."""

    parametros: Mapping[str, object]
    metricas: ResultadoAvaliacao
    resultado_objetivo: ResultadoObjetivo


@dataclass(frozen=True, slots=True)
class ResultadoOtimizacao:
    """Resultado final contendo o modelo campeão e histórico de busca."""

    melhor_modelo: EstrategiaAgrupamento
    melhores_parametros: Mapping[str, object]
    melhores_metricas: ResultadoAvaliacao
    score_campeao: float
    historico_tentativas: Sequence[CandidatoHiperparametros]


@final
class BuscadorParametros:
    """Executa a busca de hiperparâmetros avaliando candidatos de forma desacoplada."""

    def __init__(
        self,
        fabrica: FabricaAgrupadores | None = None,
        avaliador: AvaliadorClusters | None = None,
        avaliador_objetivo: AvaliadorObjetivo | None = None,
    ) -> None:
        self._fabrica = fabrica or FabricaAgrupadores()
        self._avaliador = avaliador or AvaliadorClusters()
        self._objetivo = avaliador_objetivo or AvaliadorObjetivo()

    def otimizar(
        self,
        nome_algoritmo: str,
        matriz_x: np.ndarray,
        grade_parametros: Sequence[Mapping[str, object]],
    ) -> ResultadoOtimizacao:
        """Avalia cada combinação de hiperparâmetros e elege o melhor modelo."""
        if not grade_parametros:
            raise ValueError(
                "A grade de parâmetros para otimização não pode estar vazia."
            )

        historico: list[CandidatoHiperparametros] = []
        melhor_modelo: EstrategiaAgrupamento | None = None
        melhores_params: Mapping[str, object] = grade_parametros[0]
        melhores_metricas: ResultadoAvaliacao | None = None
        melhor_score: float = -float("inf")

        for params in grade_parametros:
            modelo = self._fabrica.criar_agrupador(
                nome_algoritmo=nome_algoritmo,
                parametros=dict(params),
            )
            rotulos = modelo.treinar(matriz_x)
            metricas = self._avaliador.avaliar(matriz_x, rotulos)
            score_obj = self._objetivo.calcular_score(metricas)

            candidato = CandidatoHiperparametros(
                parametros=params,
                metricas=metricas,
                resultado_objetivo=score_obj,
            )
            historico.append(candidato)

            if score_obj.valido and score_obj.score_composto > melhor_score:
                melhor_score = score_obj.score_composto
                melhor_modelo = modelo
                melhores_params = params
                melhores_metricas = metricas

        # Se nenhum candidato foi considerado válido, assume o primeiro
        if melhor_modelo is None or melhores_metricas is None:
            primeiro = historico[0]
            melhor_modelo = self._fabrica.criar_agrupador(
                nome_algoritmo=nome_algoritmo,
                parametros=dict(primeiro.parametros),
            )
            melhor_modelo.treinar(matriz_x)
            melhores_params = primeiro.parametros
            melhores_metricas = primeiro.metricas
            melhor_score = primeiro.resultado_objetivo.score_composto

        return ResultadoOtimizacao(
            melhor_modelo=melhor_modelo,
            melhores_parametros=melhores_params,
            melhores_metricas=melhores_metricas,
            score_campeao=melhor_score,
            historico_tentativas=historico,
        )
