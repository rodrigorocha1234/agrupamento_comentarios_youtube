from typing import override

from app.contratos.fonte_dados import ProtocoloFonteDados
from app.contratos.tipos_dados import DicionarioJson, RegistroDado
from app.excecoes import ErroConexaoFonte
from app.ingestao_fontes.cliente_http_resiliente import ClienteHTTPResiliente


class AdaptadorSteam(ProtocoloFonteDados):
    """Implementa a extração de avaliações da Steam via paginação por cursor."""

    def __init__(
        self,
        cliente_http: ClienteHTTPResiliente,
        endpoint_base: str = "https://store.steampowered.com/appreviews/{appid}",
        parametros_adicionais: dict[str, str | int | float | bool] | None = None,
    ) -> None:
        self._cliente = cliente_http
        self._endpoint_base = endpoint_base
        self._parametros_adicionais = parametros_adicionais or {}

    @override
    def extrair_lote(
        self,
        identificador_origem: str | int,
        marcador_posicao: str | None = None,
        limite: int = 100,
    ) -> tuple[list[RegistroDado], str | None, bool]:
        """Extrai um lote de avaliações da Steam para o appid informado.

        Args:
            identificador_origem: AppID do jogo na Steam (ex: 730 para CS:GO, 570 para Dota 2).
            marcador_posicao: Cursor de paginação da Steam ('*' para primeira página).
            limite: Quantidade máxima de registros a solicitar (máx Steam: 100).

        Retorna:
            Tupla com (lista de reviews achatadas, próximo cursor, flag indicando se há mais páginas).
        """
        appid = int(identificador_origem)
        cursor = marcador_posicao if marcador_posicao else "*"

        url = self._resolver_url(appid)
        parametros: dict[str, str | int | float | bool] = {
            "json": 1,
            "cursor": cursor,
            "num_per_page": min(limite, 100),
            "filter": "recent",
            "language": "all",
            "review_type": "all",
            "purchase_type": "all",
        }
        for chave, valor in self._parametros_adicionais.items():
            parametros[chave] = valor

        # Garante parâmetro de paginação atualizado
        parametros["cursor"] = cursor
        parametros["num_per_page"] = min(limite, 100)

        dados_resposta = self._cliente.requisitar_json("GET", url, parametros=parametros)

        sucesso = dados_resposta.get("success")
        if sucesso not in (1, True, "1"):
            raise ErroConexaoFonte(
                f"A Steam API retornou status de falha para appid {appid}: {dados_resposta}"
            )

        reviews_brutas = dados_resposta.get("reviews")
        if not isinstance(reviews_brutas, list):
            return [], None, False

        registros_achatados: list[RegistroDado] = []
        for item in reviews_brutas:
            if isinstance(item, dict):
                registros_achatados.append(self._achatar_registro_review(appid, item))

        proximo_cursor_bruto = dados_resposta.get("cursor")
        proximo_cursor = str(proximo_cursor_bruto) if proximo_cursor_bruto else None

        # Condição de parada da Steam: sem reviews retornadas ou cursor repetido/nulo
        tem_mais = bool(registros_achatados and proximo_cursor and proximo_cursor != cursor)

        return registros_achatados, proximo_cursor, tem_mais

    @override
    def coletar_lote(
        self,
        appid: int,
        cursor: str,
        quantidade_por_pagina: int,
    ) -> tuple[list[RegistroDado], str, bool]:
        """Método de compatibilidade para chamadas orientadas a cursor explícito."""
        registros, prox_cursor, tem_mais = self.extrair_lote(
            identificador_origem=appid,
            marcador_posicao=cursor,
            limite=quantidade_por_pagina,
        )
        return registros, prox_cursor or "", tem_mais

    def _resolver_url(self, appid: int) -> str:
        """Formata a URL do endpoint substituindo o marcador {appid} ou concatenando."""
        if "{appid}" in self._endpoint_base:
            return self._endpoint_base.format(appid=appid)
        return f"{self._endpoint_base.rstrip('/')}/appreviews/{appid}"

    @staticmethod
    def _achatar_registro_review(appid: int, review_dict: DicionarioJson) -> RegistroDado:
        """Achata a estrutura aninhada de 'author' e normaliza os tipos de campos."""
        resultado: RegistroDado = {"appid": appid}

        for chave, valor in review_dict.items():
            if chave == "author" and isinstance(valor, dict):
                # Achata atributos do autor (steamid, playtime_forever, etc.)
                for chave_autor, valor_autor in valor.items():
                    if isinstance(valor_autor, (str, int, float, bool)) or valor_autor is None:
                        resultado[chave_autor] = valor_autor
                    else:
                        resultado[chave_autor] = str(valor_autor)
            elif isinstance(valor, (str, int, float, bool)) or valor is None:
                resultado[chave] = valor
            else:
                resultado[chave] = str(valor)

        # Garante que recommendationid seja sempre string para evitar perda de precisão
        if "recommendationid" in resultado:
            resultado["recommendationid"] = str(resultado["recommendationid"])

        if "steamid" in resultado:
            resultado["steamid"] = str(resultado["steamid"])

        return resultado
