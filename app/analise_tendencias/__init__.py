"""Pacote de análise e cálculo de evolução temporal de tendências."""

from app.analise_tendencias.agregador_visoes import AgregadorVisoes
from app.analise_tendencias.calculador_tendencias import CalculadorTendencias
from app.analise_tendencias.detector_variacao import (
    DetectorVariacao,
    ResultadoVariacao,
)

from app.analise_tendencias.estrategias_analise import (
    EstrategiaAnaliseClusters,
    EstrategiaAnaliseEstatica,
    EstrategiaAnaliseTemporal,
    FabricaEstrategiaAnalise,
    ResultadoAnaliseCluster,
)

__all__ = [
    "AgregadorVisoes",
    "CalculadorTendencias",
    "DetectorVariacao",
    "ResultadoVariacao",
    "EstrategiaAnaliseClusters",
    "EstrategiaAnaliseEstatica",
    "EstrategiaAnaliseTemporal",
    "FabricaEstrategiaAnalise",
    "ResultadoAnaliseCluster",
]
