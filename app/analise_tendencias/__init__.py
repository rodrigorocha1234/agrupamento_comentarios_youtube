"""Pacote de análise e cálculo de evolução temporal de tendências."""

from app.analise_tendencias.agregador_visoes import AgregadorVisoes
from app.analise_tendencias.calculador_tendencias import CalculadorTendencias
from app.analise_tendencias.detector_variacao import (
    DetectorVariacao,
    ResultadoVariacao,
)

__all__ = [
    "AgregadorVisoes",
    "CalculadorTendencias",
    "DetectorVariacao",
    "ResultadoVariacao",
]
