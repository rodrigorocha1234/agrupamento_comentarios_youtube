"""Fábrica e Registry GoF de provedores e clientes de extração da API Steam."""

from collections.abc import Callable
from typing import Final, final

from app.dominio_contratos.protocolos_extracao import ClienteSteam, GeradorPaginas
from app.extracao_steam.cliente_http import ClienteHttpSteam
from app.extracao_steam.controlador_resiliencia import ControladorResiliencia
from app.extracao_steam.gerador_paginas import GeradorPaginasSteam


class ErroProvedorExtracaoNaoRegistrado(Exception):
    """Exceção levantada quando um tipo de API ou provedor de extração não estiver registrado."""


TipoCriadorExtracao = Callable[[int, int], GeradorPaginas]


@final
class FabricaExtracao:
    """Registry e Factory GoF para desacoplar a criação de clientes e geradores de páginas Steam."""

    def __init__(self) -> None:
        self._registro: Final[dict[str, TipoCriadorExtracao]] = {}
        self._registrar_padroes()

    def registrar_provedor(
        self, nome_provedor: str, criador: TipoCriadorExtracao
    ) -> None:
        """Registra um novo provedor de extração ou cliente de API no catálogo."""
        self._registro[nome_provedor.lower().strip()] = criador

    def criar_gerador(
        self,
        nome_provedor: str = "web_api",
        limite_paginas: int = 10000,
        tamanho_pagina: int = 100,
    ) -> GeradorPaginas:
        """Instancia o gerador de páginas desacoplado conforme o provedor registrado."""
        chave = nome_provedor.lower().strip()
        criador = self._registro.get(chave)
        if criador is None:
            raise ErroProvedorExtracaoNaoRegistrado(
                f"Provedor de extração da Steam '{nome_provedor}' não foi registrado no catálogo."
            )
        return criador(limite_paginas, tamanho_pagina)

    def _registrar_padroes(self) -> None:
        """Registra as implementações padrão da Steamworks Web API."""

        def _criar_web_api(limite_paginas: int, tamanho_pagina: int) -> GeradorPaginas:
            controlador = ControladorResiliencia(
                max_tentativas=5,
                espera_base_segundos=1.0,
            )
            cliente: ClienteSteam = ClienteHttpSteam(controlador_resiliencia=controlador)
            return GeradorPaginasSteam(
                cliente=cliente,
                maximo_paginas=limite_paginas,
                tamanho_pagina=tamanho_pagina,
            )

        self.registrar_provedor("web_api", _criar_web_api)
        self.registrar_provedor("steam_oficial", _criar_web_api)
