"""Contratos e protocolos para fontes de dados externas."""

from typing import Protocol, runtime_checkable

from app.contratos.tipos_dados import RegistroDado


@runtime_checkable
class ProtocoloFonteDados(Protocol):
    """Protocolo abstrato (Strategy) para ingestão de dados de qualquer fonte (API Steam, Bancos SQL, APIs REST)."""

    def extrair_lote(
        self,
        identificador_origem: str | int,
        marcador_posicao: str | None = None,
        limite: int = 100,
    ) -> tuple[list[RegistroDado], str | None, bool]:
        """Extrai um lote de registros da fonte informada.

        Args:
            identificador_origem: Identificador do recurso (ex: appid na Steam, tabela/query em DB, ID de projeto).
            marcador_posicao: Cursor de paginação, offset numérico ou timestamp incremental.
            limite: Quantidade máxima de registros a recuperar no lote.

        Retorna:
            Tupla contendo (lista de registros brutos, próximo marcador/cursor ou None, booleano indicando se há mais registros).
        """
        ...

    def coletar_lote(
        self,
        appid: int,
        cursor: str,
        quantidade_por_pagina: int,
    ) -> tuple[list[RegistroDado], str, bool]:
        """Método de compatibilidade para APIs com cursor explícito."""
        ...
