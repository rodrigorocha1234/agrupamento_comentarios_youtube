"""Gerador paginado lazy por cursor com detecção de repetições e respeito a backpressure."""

from collections.abc import Iterator
from typing import Final, final

from app.dominio_contratos.modelos_dados import PaginaReviews
from app.dominio_contratos.protocolos_extracao import ClienteSteam
from app.extracao_steam.adaptador_steam import AdaptadorSteam


@final
class GeradorPaginasSteam:
    """Implementa consumo incremental via Iterator[PaginaReviews], sem carregar páginas em memória."""

    def __init__(
        self,
        cliente: ClienteSteam,
        adaptador: AdaptadorSteam | None = None,
        maximo_paginas: int = 10000,
        tamanho_pagina: int = 100,
        filtro: str = "recent",
        idiomas: tuple[str, ...] = ("brazilian",),
    ) -> None:
        self._cliente: Final[ClienteSteam] = cliente
        self._adaptador: Final[AdaptadorSteam] = adaptador or AdaptadorSteam()
        self._maximo_paginas: Final[int] = maximo_paginas
        self._tamanho_pagina: Final[int] = tamanho_pagina
        self._filtro: Final[str] = filtro
        self._idiomas: Final[tuple[str, ...]] = idiomas

    def iterar_paginas(
        self, appid: int, cursor_inicial: str = "*"
    ) -> Iterator[PaginaReviews]:
        """Gera páginas de reviews sob demanda até esgotamento ou limite configurado."""
        cursor_atual = cursor_inicial
        cursores_visitados: set[str] = set()
        paginas_emitidas = 0

        while cursor_atual not in cursores_visitados:
            cursores_visitados.add(cursor_atual)
            dados_brutos = self._cliente.buscar_pagina_bruta(
                appid=appid,
                cursor=cursor_atual,
                tamanho_pagina=self._tamanho_pagina,
            )

            pagina = self._adaptador.converter_pagina(
                appid=appid,
                cursor_entrada=cursor_atual,
                dados_brutos=dados_brutos,
            )

            if not pagina.reviews:
                return

            yield pagina
            paginas_emitidas += 1

            if paginas_emitidas >= self._maximo_paginas:
                return

            if pagina.cursor_proximo is None or pagina.cursor_proximo == cursor_atual:
                return

            cursor_atual = pagina.cursor_proximo
