"""Fábrica e Registry de provedores de staging sem seleção por if/elif no domínio."""

from collections.abc import Callable
from typing import Final, final

from app.dominio_contratos.protocolos_staging import RepositorioStaging, UnidadeTrabalho
from app.persistencia_staging.conexao_sqlite import ConexaoSqlite
from app.persistencia_staging.esquema_tabelas import EsquemaTabelasStaging
from app.persistencia_staging.repositorio_sqlite import RepositorioStagingSqlite
from app.persistencia_staging.unidade_trabalho import UnidadeTrabalhoSqlite

TipoCriadorStaging = Callable[[], tuple[UnidadeTrabalho, RepositorioStaging]]


class ErroTecnologiaStagingNaoRegistrada(Exception):
    """Exceção levantada quando um driver ou tecnologia de banco não estiver no registro."""


@final
class FabricaStaging:
    """Registry e Factory para instanciar repositórios e unidades de trabalho."""

    def __init__(self) -> None:
        self._registro: Final[dict[str, TipoCriadorStaging]] = {}
        self._registrar_padroes()

    def registrar_tecnologia(
        self, nome_tecnologia: str, criador: TipoCriadorStaging
    ) -> None:
        """Adiciona uma nova implementação ao catálogo."""
        self._registro[nome_tecnologia.lower()] = criador

    def criar_staging(
        self, nome_tecnologia: str
    ) -> tuple[UnidadeTrabalho, RepositorioStaging]:
        """Resolve a implementação registrada sem encadeamento de if/elif."""
        chave = nome_tecnologia.lower()
        criador = self._registro.get(chave)
        if criador is None:
            raise ErroTecnologiaStagingNaoRegistrada(
                f"Tecnologia de staging '{nome_tecnologia}' não foi registrada no sistema."
            )
        return criador()

    def _registrar_padroes(self) -> None:
        """Registra a implementação padrão de SQLite."""

        def _criar_sqlite() -> tuple[UnidadeTrabalho, RepositorioStaging]:
            gerenciador = ConexaoSqlite()
            conexao = gerenciador.criar_conexao()
            esquema = EsquemaTabelasStaging()
            esquema.inicializar_esquema(conexao)
            uow = UnidadeTrabalhoSqlite(conexao)
            repositorio = RepositorioStagingSqlite(conexao)
            return uow, repositorio

        self.registrar_tecnologia("sqlite", _criar_sqlite)
