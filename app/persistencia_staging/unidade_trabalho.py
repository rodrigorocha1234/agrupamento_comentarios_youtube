"""Implementação do padrão Unit of Work para delimitação transacional no SQLite."""

import sqlite3
from types import TracebackType
from typing import final, override

from app.dominio_contratos.protocolos_staging import UnidadeTrabalho


@final
class UnidadeTrabalhoSqlite(UnidadeTrabalho):
    """Controla o ciclo de vida de transações atômicas no SQLite."""

    def __init__(self, conexao: sqlite3.Connection) -> None:
        self._conexao = conexao
        self._em_transacao = False

    @property
    def conexao(self) -> sqlite3.Connection:
        """Fornece acesso à conexão ativa vinculada à unidade de trabalho."""
        return self._conexao

    @override
    def __enter__(self) -> "UnidadeTrabalhoSqlite":
        self._em_transacao = True
        return self

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        if exc_type is not None:
            self.reverter()
            return False
        if self._em_transacao:
            self.confirmar()
        return None

    @override
    def confirmar(self) -> None:
        """Comita as alterações pendentes na conexão."""
        if self._em_transacao:
            self._conexao.commit()
            self._em_transacao = False

    @override
    def reverter(self) -> None:
        """Desfaz as operações pendentes em caso de erro."""
        if self._em_transacao:
            self._conexao.rollback()
            self._em_transacao = False
