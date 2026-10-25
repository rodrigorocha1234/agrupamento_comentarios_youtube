"""Contratos para motores de processamento tabular (Pandas/Polars)."""

from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class ProtocoloMotorProcessamento(Protocol):
    """Protocolo abstrato para manipulação tabular de dados do Lakehouse."""

    def carregar_dados(self, caminho_arquivo: str) -> pd.DataFrame:
        """Carrega dados a partir de um arquivo Parquet."""
        ...

    def salvar_dados(self, dados: pd.DataFrame, caminho_arquivo: str) -> None:
        """Persiste dados em formato Parquet."""
        ...

    def deduplicar(self, dados: pd.DataFrame, coluna_chave: str) -> pd.DataFrame:
        """Deduplica registros mantendo a ocorrência mais recente."""
        ...

    def selecionar_colunas(self, dados: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
        """Filtra apenas as colunas especificadas que existirem no DataFrame."""
        ...
