"""Gerenciador de conexão SQLite com WAL, busy_timeout e integridade referencial."""

import sqlite3
from pathlib import Path
from typing import final


@final
class ConexaoSqlite:
    """Gerencia a conexão SQLite garantindo configurações de concorrência adequadas."""

    def __init__(
        self,
        caminho_banco: str | Path = "./dados_staging/staging_steam.db",
        modo_journal: str = "WAL",
        timeout_segundos: float = 30.0,
    ) -> None:
        self._caminho = Path(caminho_banco).resolve()
        self._modo_journal = modo_journal
        self._timeout = timeout_segundos

    @property
    def caminho(self) -> Path:
        """Caminho absoluto do arquivo de banco de dados."""
        return self._caminho

    def criar_conexao(self) -> sqlite3.Connection:
        """Cria e configura uma nova conexão com o SQLite."""
        self._caminho.parent.mkdir(parents=True, exist_ok=True)
        conexao = sqlite3.connect(
            str(self._caminho),
            timeout=self._timeout,
            autocommit=False,
        )
        conexao.row_factory = sqlite3.Row
        with conexao:
            conexao.execute(f"PRAGMA journal_mode = {self._modo_journal};")
            conexao.execute(f"PRAGMA busy_timeout = {int(self._timeout * 1000)};")
            conexao.execute("PRAGMA foreign_keys = ON;")
        return conexao
