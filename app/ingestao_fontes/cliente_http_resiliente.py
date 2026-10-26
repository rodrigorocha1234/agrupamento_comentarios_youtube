"""Cliente HTTP resiliente com retries exponenciais, tratamento de rate limit e timeouts."""

import time
from types import TracebackType
from typing import Final, Self

import httpx

from app.contratos.tipos_dados import DicionarioJson
from app.excecoes import ErroConexaoFonte

STATUS_RETENTAVEIS: Final[set[int]] = {429, 500, 502, 503, 504}


class ClienteHTTPResiliente:
    """Cliente HTTP com suporte a tolerância a falhas, retries com backoff e rate limiting."""

    def __init__(
        self,
        timeout_segundos: float = 30.0,
        tentativas_maximas: int = 5,
        espera_base_segundos: float = 1.0,
        headers_padrao: dict[str, str] | None = None,
        cliente_httpx: httpx.Client | None = None,
    ) -> None:
        self.timeout_segundos = timeout_segundos
        self.tentativas_maximas = max(1, tentativas_maximas)
        self.espera_base_segundos = max(0.1, espera_base_segundos)
        self.headers_padrao = headers_padrao or {}
        self._cliente = cliente_httpx or httpx.Client(
            timeout=self.timeout_segundos,
            headers=self.headers_padrao,
            follow_redirects=True,
        )

    def fechar(self) -> None:
        """Encerra a sessão HTTP subjacente."""
        self._cliente.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.fechar()

    def requisitar_json(
        self,
        metodo: str,
        url: str,
        parametros: dict[str, str | int | float | bool] | None = None,
        headers: dict[str, str] | None = None,
    ) -> DicionarioJson:
        """Executa uma requisição HTTP retornando a resposta decodificada em JSON.

        Aplica retries exponenciais automáticos em caso de erros temporários ou status 429/5xx.
        """
        cabecalhos = dict(self.headers_padrao)
        if headers:
            cabecalhos.update(headers)

        ultima_excecao: Exception | None = None

        for tentativa in range(1, self.tentativas_maximas + 1):
            try:
                resposta = self._cliente.request(
                    method=metodo.upper(),
                    url=url,
                    params=parametros,
                    headers=cabecalhos,
                )

                if resposta.status_code in STATUS_RETENTAVEIS:
                    tempo_espera = self._calcular_tempo_espera(tentativa, resposta)
                    time.sleep(tempo_espera)
                    continue

                resposta.raise_for_status()
                conteudo = resposta.json()
                if isinstance(conteudo, dict):
                    return conteudo
                raise ErroConexaoFonte(
                    f"A resposta de '{url}' não é um objeto JSON válido (recebido: {type(conteudo)})."
                )

            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                ultima_excecao = exc
                if tentativa < self.tentativas_maximas:
                    tempo_espera = self.espera_base_segundos * (2 ** (tentativa - 1))
                    time.sleep(tempo_espera)
                else:
                    break

        mensagem_erro = (
            f"Falha após {self.tentativas_maximas} tentativas ao acessar '{url}'."
            + (f" Causa: {ultima_excecao}" if ultima_excecao else "")
        )
        raise ErroConexaoFonte(mensagem_erro) from ultima_excecao

    def _calcular_tempo_espera(self, tentativa: int, resposta: httpx.Response) -> float:
        """Determina o tempo de espera respeitando o header Retry-After se fornecido."""
        if resposta.status_code == 429:
            retry_after = resposta.headers.get("Retry-After")
            if retry_after:
                try:
                    return max(float(retry_after), 0.5)
                except ValueError:
                    pass
        return self.espera_base_segundos * (2 ** (tentativa - 1))
