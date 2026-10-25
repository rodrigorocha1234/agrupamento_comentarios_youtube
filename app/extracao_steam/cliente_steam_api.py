"""Adaptador de compatibilidade para cliente de API da Steam."""

from app.ingestao_fontes.adaptadores.adaptador_steam import AdaptadorSteam
from app.ingestao_fontes.cliente_http_resiliente import ClienteHTTPResiliente


class ClienteSteamAPI(AdaptadorSteam):
    """Cliente HTTP com suporte a cursor, retries e rate limit para a Steam Web API."""

    def __init__(
        self,
        endpoint_base: str = "https://store.steampowered.com/appreviews/{appid}",
        timeout_segundos: float = 30.0,
        tentativas_maximas: int = 5,
        espera_base_segundos: float = 1.0,
        parametros_adicionais: dict[str, str | int | float | bool] | None = None,
        cliente_resiliente: ClienteHTTPResiliente | None = None,
    ) -> None:
        cliente = cliente_resiliente or ClienteHTTPResiliente(
            timeout_segundos=timeout_segundos,
            tentativas_maximas=tentativas_maximas,
            espera_base_segundos=espera_base_segundos,
        )
        super().__init__(
            cliente_http=cliente,
            endpoint_base=endpoint_base,
            parametros_adicionais=parametros_adicionais,
        )
