"""Contratos e protocolos para fontes de dados externas."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProtocoloFonteDados(Protocol):
    """Protocolo abstrato para adaptadores de ingestão de avaliações."""

    def coletar_lote(
        self,
        appid: int,
        cursor: str,
        quantidade_por_pagina: int,
    ) -> tuple[list[dict[str, object]], str, bool]:
        """Coleta um lote de avaliações para o appid informado.

        Retorna:
            Uma tupla contendo a lista de registros brutos, o próximo cursor e se há mais páginas.
        """
        ...
