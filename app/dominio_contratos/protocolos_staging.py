"""Protocolos para demarcação transacional (Unit of Work) e repositório de staging."""

from collections.abc import Sequence
from types import TracebackType
from typing import Protocol, Self, TypeVar

from app.dominio_contratos.modelos_dados import (
    EventoPublicacao,
    MetadadosExecucao,
    PaginaReviews,
    ReviewSteam,
)

T_co = TypeVar("T_co", covariant=True)


class UnidadeTrabalho(Protocol):
    """Contrato do Unit of Work para delimitação atômica de transações."""

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None: ...

    def confirmar(self) -> None:
        """Efetiva as operações no banco transacional."""
        ...

    def reverter(self) -> None:
        """Desfaz as operações pendentes em caso de erro."""
        ...


class RepositorioStaging(Protocol):
    """Contrato para persistência e leitura das tabelas de staging transacional."""

    def registrar_execucao(self, metadados: MetadadosExecucao) -> None:
        """Grava ou atualiza os dados da sessão de coleta."""
        ...

    def gravar_pagina(self, pagina: PaginaReviews, id_execucao: str) -> None:
        """Persiste metadados da página recebida de forma idempotente."""
        ...

    def salvar_lote_reviews(self, reviews: Sequence[ReviewSteam]) -> int:
        """Persiste ou atualiza lote de avaliações nas tabelas atuais e históricas."""
        ...

    def atualizar_checkpoint(
        self, appid: int, estrategia: str, cursor: str, status: str
    ) -> None:
        """Grava marcador estável de progresso para retomada após falhas."""
        ...

    def obter_ultimo_checkpoint(self, appid: int, estrategia: str) -> str | None:
        """Recupera o último cursor gravado com sucesso."""
        ...

    def enfileirar_evento_outbox(self, evento: EventoPublicacao) -> None:
        """Adiciona um evento na tabela de outbox na mesma transação."""
        ...

    def obter_eventos_pendentes(self, limite: int) -> Sequence[EventoPublicacao]:
        """Lê eventos pendentes da outbox para publicação."""
        ...

    def marcar_evento_publicado(self, id_evento: str) -> None:
        """Atualiza o evento na outbox após confirmação no Data Lake."""
        ...
