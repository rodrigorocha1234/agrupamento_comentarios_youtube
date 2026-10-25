"""Implementação do padrão Unit of Work para demarcação transacional em PostgreSQL."""

from types import TracebackType
from typing import Self, final, override

import psycopg

from app.dominio_contratos.modelos_dados import TipoParametroSql
from app.dominio_contratos.protocolos_staging import UnidadeTrabalho


@final
class UnidadeTrabalhoPostgres(UnidadeTrabalho):
    """Controla o ciclo de vida e a atomicidade de transações no banco PostgreSQL."""

    def __init__(self, conexao: psycopg.Connection[tuple[TipoParametroSql, ...]]) -> None:
        self._conexao = conexao


    @override
    def __enter__(self) -> Self:
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
        self.confirmar()
        return None

    @override
    def confirmar(self) -> None:
        """Efetiva as operações pendentes com commit."""
        self._conexao.commit()

    @override
    def reverter(self) -> None:
        """Desfaz as alterações pendentes em caso de erro."""
        self._conexao.rollback()
