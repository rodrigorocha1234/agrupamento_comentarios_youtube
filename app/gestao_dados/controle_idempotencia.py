"""Controle de idempotência e detecção de versões de comentários."""

from dataclasses import dataclass
from datetime import datetime
from app.coleta_youtube.modelos_coleta import ComentarioColetado


@dataclass(frozen=True, slots=True)
class RegistroVersao:
    """Metadados para aferição de imutabilidade e novas versões de um comentário."""

    id_comentario: str
    id_video: str
    etag: str
    hash_conteudo: str
    atualizado_em: datetime


class ControleIdempotencia:
    """Avalia comentários coletados contra o estado anterior conhecido para evitar duplicatas."""

    @staticmethod
    def verificar_alteracao(
        comentario: ComentarioColetado,
        versao_anterior: RegistroVersao | None,
    ) -> bool:
        """Determina se o comentário é novo ou se sofreu alteração de conteúdo/timestamp.

        Returns:
            True se o comentário for novo ou tiver mudado etag/hash/timestamp; False se inalterado.
        """
        if versao_anterior is None:
            return True

        if comentario.hash_conteudo != versao_anterior.hash_conteudo:
            return True

        if comentario.etag != versao_anterior.etag and versao_anterior.etag != "":
            return True

        if comentario.atualizado_em > versao_anterior.atualizado_em:
            return True

        return False
