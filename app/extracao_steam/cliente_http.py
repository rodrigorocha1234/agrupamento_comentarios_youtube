"""Cliente HTTP para o serviço GetAppReviews da Web API do Steamworks."""

import json
from typing import Final, final

import requests

from app.extracao_steam.controlador_resiliencia import ControladorResiliencia


@final
class ClienteHttpSteam:
    """Consome o endpoint oficial IUserReviewsService/GetAppReviews/v1 com input_json."""

    _URL_BASE: Final[str] = (
        "https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/"
    )

    def __init__(
        self,
        chave_api: str | None = None,
        timeout_segundos: int = 30,
        controlador_resiliencia: ControladorResiliencia | None = None,
        sessao_customizada: requests.Session | None = None,
    ) -> None:
        self._chave_api = chave_api if chave_api else None
        self._timeout = timeout_segundos
        self._resiliencia = controlador_resiliencia or ControladorResiliencia()
        self._sessao = sessao_customizada or requests.Session()

    def buscar_pagina_bruta(
        self,
        appid: int,
        cursor: str = "*",
        tamanho_pagina: int = 100,
        filtro: str = "recent",
        idiomas: tuple[str, ...] = ("brazilian",),
    ) -> dict[str, object]:
        """Executa a requisição GET com tratamento de backpressure e 429."""
        parametros_corpo: dict[str, object] = {
            "appid": appid,
            "cursor": cursor,
            "num_per_page": min(tamanho_pagina, 100),
            "filter": filtro,
            "languages": list(idiomas),
            "review_type": "all",
            "purchase_type": "all",
            "filter_offtopic_activity": True,
        }

        query_params: dict[str, str] = {
            "input_json": json.dumps(parametros_corpo, separators=(",", ":"))
        }
        if self._chave_api:
            query_params["key"] = self._chave_api

        tentativa = 1
        while True:
            try:
                resposta = self._sessao.get(
                    self._URL_BASE,
                    params=query_params,
                    timeout=self._timeout,
                )

                if resposta.status_code == 429:
                    self._resiliencia.esperar_por_taxa_limite()
                    tentativa += 1
                    self._resiliencia.executar_pausa_tentativa(tentativa)
                    continue

                resposta.raise_for_status()
                dados_json = resposta.json()
                if not isinstance(dados_json, dict):
                    raise TypeError(
                        "A resposta da API da Steam deve ser um objeto JSON."
                    )

                dados_tipados: dict[str, object] = {}
                for k, v in dados_json.items():
                    if isinstance(k, str):
                        dados_tipados[k] = v
                return dados_tipados

            except (requests.RequestException, TypeError, ValueError):
                self._resiliencia.executar_pausa_tentativa(tentativa)
                tentativa += 1
