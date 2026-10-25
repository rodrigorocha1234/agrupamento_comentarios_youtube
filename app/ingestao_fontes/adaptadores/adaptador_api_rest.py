"""Adaptador de fonte de dados para APIs REST genéricas com paginação configurável."""

from typing import override

from app.contratos.fonte_dados import ProtocoloFonteDados
from app.ingestao_fontes.cliente_http_resiliente import ClienteHTTPResiliente


class AdaptadorAPIRest(ProtocoloFonteDados):
    """Implementa a extração genérica de dados via endpoints REST paginados."""

    def __init__(
        self,
        cliente_http: ClienteHTTPResiliente,
        endpoint: str,
        metodo: str = "GET",
        parametro_paginacao: str = "cursor",
        parametro_limite: str = "limite",
        campo_resposta_dados: str = "itens",
        campo_resposta_proximo_cursor: str = "proximo_cursor",
        headers: dict[str, str] | None = None,
        parametros_fixos: dict[str, str | int | float | bool] | None = None,
    ) -> None:
        self._cliente = cliente_http
        self._endpoint = endpoint
        self._metodo = metodo
        self._parametro_paginacao = parametro_paginacao
        self._parametro_limite = parametro_limite
        self._campo_resposta_dados = campo_resposta_dados
        self._campo_resposta_proximo_cursor = campo_resposta_proximo_cursor
        self._headers = headers or {}
        self._parametros_fixos = parametros_fixos or {}

    @override
    def extrair_lote(
        self,
        identificador_origem: str | int,
        marcador_posicao: str | None = None,
        limite: int = 100,
    ) -> tuple[list[dict[str, object]], str | None, bool]:
        """Extrai lote de dados da API REST utilizando marcador de paginação."""
        url = self._formatar_url(identificador_origem)

        parametros: dict[str, str | int | float | bool] = dict(self._parametros_fixos)
        parametros[self._parametro_limite] = limite

        if marcador_posicao:
            parametros[self._parametro_paginacao] = marcador_posicao

        resposta = self._cliente.requisitar_json(
            metodo=self._metodo,
            url=url,
            parametros=parametros,
            headers=self._headers,
        )

        itens_brutos = resposta.get(self._campo_resposta_dados)
        if not isinstance(itens_brutos, list):
            # Tenta campos comuns como fallback ('items', 'data', 'reviews', 'comentarios')
            for chave_candidata in ("items", "data", "reviews", "comentarios", "results"):
                candidato = resposta.get(chave_candidata)
                if isinstance(candidato, list):
                    itens_brutos = candidato
                    break

        registros: list[dict[str, object]] = []
        if isinstance(itens_brutos, list):
            for item in itens_brutos:
                if isinstance(item, dict):
                    registros.append(dict(item))

        proximo_cursor_bruto = (
            resposta.get(self._campo_resposta_proximo_cursor)
            or resposta.get("nextPageToken")
            or resposta.get("next_cursor")
            or resposta.get("cursor")
        )
        proximo_cursor = str(proximo_cursor_bruto) if proximo_cursor_bruto else None

        tem_mais = bool(registros and proximo_cursor and proximo_cursor != marcador_posicao)
        return registros, proximo_cursor, tem_mais

    @override
    def coletar_lote(
        self,
        appid: int,
        cursor: str,
        quantidade_por_pagina: int,
    ) -> tuple[list[dict[str, object]], str, bool]:
        registros, prox_cursor, tem_mais = self.extrair_lote(
            identificador_origem=appid,
            marcador_posicao=cursor,
            limite=quantidade_por_pagina,
        )
        return registros, prox_cursor or "", tem_mais

    def _formatar_url(self, identificador_origem: str | int) -> str:
        ident_str = str(identificador_origem)
        if "{identificador}" in self._endpoint:
            return self._endpoint.format(identificador=ident_str)
        if "{id}" in self._endpoint:
            return self._endpoint.format(id=ident_str)
        return self._endpoint
