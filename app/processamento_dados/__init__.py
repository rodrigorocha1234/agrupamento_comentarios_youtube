"""Módulo de processamento tabular de dados com suporte a motores Pandas e Polars."""

from app.processamento_dados.avaliador_expressao import AvaliadorExpressao
from app.processamento_dados.processador_tabela import ProcessadorTabela

__all__ = [
    "AvaliadorExpressao",
    "ProcessadorTabela",
]
