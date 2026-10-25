"""Contratos para persistência de dados nas camadas do Lakehouse."""

from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class ProtocoloRepositorioLakehouse(Protocol):
    """Protocolo abstrato para gerenciamento remoto das camadas Bronze, Silver e Gold no RustFS/S3."""

    def gravar_bronze(self, appid: int, registros: list[dict[str, object]]) -> str:
        """Grava dados brutos na camada Bronze no RustFS/S3 e retorna a URI gravada (s3://...)."""
        ...

    def gravar_silver(self, appid: int, dados: pd.DataFrame) -> str:
        """Grava dados limpos e tipados na camada Silver no RustFS/S3 e retorna a URI gravada (s3://...)."""
        ...

    def gravar_gold(self, appid: int, dados: pd.DataFrame, sufixo_visao: str) -> str:
        """Grava matriz de atributos ou resultados finais na camada Gold no RustFS/S3 e retorna a URI (s3://...)."""
        ...

    def ler_silver(self, appid: int) -> pd.DataFrame:
        """Lê os dados da camada Silver para o appid informado a partir do RustFS/S3."""
        ...

    def ler_gold(self, appid: int, sufixo_visao: str) -> pd.DataFrame:
        """Lê visão específica da camada Gold para o appid informado a partir do RustFS/S3."""
        ...
