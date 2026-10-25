"""Protocolos para persistência no Data Lake e processamento de outbox."""

from collections.abc import Sequence
from typing import Protocol

from app.dominio_contratos.modelos_dados import EventoPublicacao


class ArmazenamentoLake(Protocol):
    """Contrato abstrato de armazenamento de objetos no Data Lake (RustFS/S3)."""

    @property
    def bucket(self) -> str:
        """Nome do bucket alvo no Data Lake."""
        ...

    def gravar_texto(self, caminho_chave: str, conteudo: str) -> None:
        """Persiste conteúdo textual (JSON, manifesto)."""
        ...

    def gravar_bytes(self, caminho_chave: str, dados_bytes: bytes) -> None:
        """Persiste conteúdo binário (Parquet)."""
        ...

    def ler_bytes(self, caminho_chave: str) -> bytes:
        """Recupera conteúdo binário de um caminho no Lakehouse/S3."""
        ...

    def listar_chaves(self, prefixo: str) -> list[str]:
        """Lista os caminhos de chaves sob o prefixo especificado."""
        ...

    def verificar_existencia(self, caminho_chave: str) -> bool:
        """Verifica se o objeto já existe no bucket."""
        ...


class PublicadorOutbox(Protocol):
    """Contrato para o consumidor que publica eventos pendentes no Data Lake."""

    def processar_lote_eventos(self, eventos: Sequence[EventoPublicacao]) -> int:
        """Publica eventos no Data Lake e marca como concluídos no staging."""
        ...
