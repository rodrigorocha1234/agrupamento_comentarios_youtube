"""Gerenciador de conexões transacionais com banco de dados PostgreSQL."""

import os
from typing import final

import psycopg

from app.dominio_contratos.modelos_dados import TipoParametroSql


@final
class ConexaoPostgresStaging:
    """Responsável por estabelecer conexões com o PostgreSQL de staging."""

    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or os.getenv(
            "STAGING_POSTGRES_DSN",
            "postgresql://mlflow:mlflow_senha@localhost:5432/mlflow",
        )

    def criar_conexao(self) -> psycopg.Connection[tuple[TipoParametroSql, ...]]:
        """Abre uma nova conexão ativa com o servidor PostgreSQL."""
        return psycopg.connect(self._dsn, autocommit=False)

