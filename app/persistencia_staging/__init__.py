"""Pacote de persistência relacional e staging transacional."""

from app.persistencia_staging.conexao_postgres import ConexaoPostgresStaging
from app.persistencia_staging.conexao_sqlite import ConexaoSqlite
from app.persistencia_staging.esquema_postgres import EsquemaTabelasPostgres
from app.persistencia_staging.esquema_tabelas import EsquemaTabelasStaging
from app.persistencia_staging.fabrica_staging import FabricaStaging
from app.persistencia_staging.repositorio_postgres import RepositorioStagingPostgres
from app.persistencia_staging.repositorio_sqlite import RepositorioStagingSqlite
from app.persistencia_staging.unidade_postgres import UnidadeTrabalhoPostgres
from app.persistencia_staging.unidade_trabalho import UnidadeTrabalhoSqlite

__all__ = [
    "ConexaoPostgresStaging",
    "ConexaoSqlite",
    "EsquemaTabelasPostgres",
    "EsquemaTabelasStaging",
    "FabricaStaging",
    "RepositorioStagingPostgres",
    "RepositorioStagingSqlite",
    "UnidadeTrabalhoPostgres",
    "UnidadeTrabalhoSqlite",
]
