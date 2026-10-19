"""Adaptador HTTP cliente para comunicação com o MLflow Model Serving (/invocations)."""

from typing import cast
import requests


class AdaptadorServingErro(Exception):
    """Exceção levantada em falhas de comunicação com o MLflow Serving."""


class AdaptadorServing:
    """Consome o endpoint /invocations do MLflow Serving com timeout e retries."""

    def __init__(
        self,
        serving_url: str = "http://127.0.0.1:8080",
        tempo_limite_segundos: float = 30.0,
        sessao_http: requests.Session | None = None,
    ) -> None:
        self._url_base: str = serving_url.rstrip("/")
        self._tempo_limite: float = tempo_limite_segundos
        self._sessao: requests.Session = sessao_http or requests.Session()

    def invocar_predicao(
        self,
        textos_comentarios: list[str],
    ) -> list[int]:
        """Envia requisição no formato padrão do MLflow Serving e extrai as predições de cluster."""
        url = f"{self._url_base}/invocations"
        payload = {
            "dataframe_split": {
                "columns": ["texto"],
                "data": [[t] for t in textos_comentarios],
            }
        }
        headers = {"Content-Type": "application/json"}

        try:
            resposta = self._sessao.post(
                url,
                json=payload,
                headers=headers,
                timeout=self._tempo_limite,
            )
            resposta.raise_for_status()

            dados_retorno: object = resposta.json()
            if isinstance(dados_retorno, dict):
                dados_dict = cast(dict[str, object], dados_retorno)
                predicoes_raw = dados_dict.get("predictions")
                if isinstance(predicoes_raw, list):
                    return [int(str(p)) for p in predicoes_raw]

            if isinstance(dados_retorno, list):
                return [int(str(p)) for p in dados_retorno]

            raise AdaptadorServingErro(
                f"Formato inesperado na resposta do serving: {dados_retorno}"
            )
        except Exception as erro:
            raise AdaptadorServingErro(
                f"Falha ao chamar endpoint de serving {url}: {erro}"
            ) from erro
