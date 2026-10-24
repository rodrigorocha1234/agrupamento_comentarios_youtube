"""Pacote de motores tabulares e processamento por DSL declarativa."""

from app.processamento_dados.fabrica_motores import FabricaMotores
from app.processamento_dados.interpretador_dsl import InterpretadorDsl
from app.processamento_dados.motor_pandas import MotorPandas
from app.processamento_dados.motor_polars import MotorPolars

__all__ = [
    "FabricaMotores",
    "InterpretadorDsl",
    "MotorPandas",
    "MotorPolars",
]
