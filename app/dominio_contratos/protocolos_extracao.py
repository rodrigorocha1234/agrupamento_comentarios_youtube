"""Protocolos e contratos formais para clientes e geradores de extração da Steam."""

from collections.abc import Iterator
from typing import Protocol, TypeVar

from app.dominio_contratos.modelos_dados import PaginaReviews

T_co = TypeVar("T_co", covariant=True)


class FonteDados(Protocol[T_co]):
    """Contrato genérico para fornecedores de fluxos iteráveis de dados."""

    def extrair_registros(self) -> Iterator[T_co]:
        """Fornece um iterador de uso único."""
        ...


class ClienteSteam(Protocol):
    """Contrato do cliente de baixo nível para a API Steam."""

    def buscar_pagina_bruta(
        self, appid: int, cursor: str, tamanho_pagina: int
    ) -> dict[str, object]:
        """Executa a requisição HTTP retornando o dicionário da resposta."""
        ...


class GeradorPaginas(Protocol):
    """Contrato para geradores de páginas com paginação lazy e controle de cursor."""

    def iterar_paginas(
        self, appid: int, cursor_inicial: str = "*"
    ) -> Iterator[PaginaReviews]:
        """Gera páginas de reviews sob demanda (lazy) respeitando backpressure."""
        ...
