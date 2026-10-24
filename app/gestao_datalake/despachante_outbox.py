"""Despachante de eventos da tabela outbox para entrega desacoplada e idempotente ao Data Lake."""

from collections.abc import Sequence
from typing import final, override

from app.dominio_contratos.modelos_dados import EventoPublicacao
from app.dominio_contratos.protocolos_datalake import (
    ArmazenamentoLake,
    PublicadorOutbox,
)
from app.dominio_contratos.protocolos_staging import RepositorioStaging


@final
class DespachanteOutbox(PublicadorOutbox):
    """Processa eventos outbox pendentes no staging e confirma entrega no S3."""

    def __init__(
        self,
        repositorio: RepositorioStaging,
        armazenamento: ArmazenamentoLake,
    ) -> None:
        self._repositorio = repositorio
        self._armazenamento = armazenamento

    @override
    def processar_lote_eventos(self, eventos: Sequence[EventoPublicacao]) -> int:
        """Entrega cada evento ao Lakehouse e atualiza seu status no staging."""
        total_publicado = 0
        for evento in eventos:
            if evento.status_publicacao == "publicado":
                continue

            # Se for evento de payload textual (Bronze)
            if evento.tipo_evento == "bronze_pagina":
                self._armazenamento.gravar_texto(
                    caminho_chave=evento.chave_origem,
                    conteudo=evento.payload_referencia,
                )
                self._repositorio.marcar_evento_publicado(evento.id_evento)
                total_publicado += 1

        return total_publicado

    def executar_ciclo_publicacao(self, limite_lote: int = 100) -> int:
        """Busca eventos pendentes do repositório e despacha para o Data Lake."""
        pendentes = self._repositorio.obter_eventos_pendentes(limite=limite_lote)
        if not pendentes:
            return 0
        return self.processar_lote_eventos(pendentes)
