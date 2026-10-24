"""Validador de coerência semântica e compatibilidade cruzada entre arquivos de configuração."""

from typing import final

from app.configuracao_geral.conf_yaml import ConfYAML


class ErroCompatibilidadeConfiguracao(Exception):
    """Exceção levantada quando configurações entre arquivos forem conflitantes."""


@final
class ValidadorCompatibilidade:
    """Valida regras de negócio e limites operacionais entre múltiplos YAMLs."""

    def __init__(self, configuracoes: ConfYAML) -> None:
        self._configuracoes = configuracoes

    def validar_todas_regras(self) -> None:
        """Executa todas as verificações cruzadas de compatibilidade."""
        self._validar_limites_fluxo()
        self._validar_coerencia_staging()
        self._validar_parametros_steam()

    def _validar_limites_fluxo(self) -> None:
        fluxos = self._configuracoes.fluxos_incrementais.fluxos_incrementais
        if fluxos.paginacao.tamanho_pagina <= 0:
            raise ErroCompatibilidadeConfiguracao(
                "O tamanho de página da coleta deve ser estritamente positivo."
            )
        if fluxos.paginacao.tamanho_pagina > 100:
            raise ErroCompatibilidadeConfiguracao(
                "A API da Steam impõe tamanho máximo de página de 100 registros."
            )
        if fluxos.staging.tamanho_lote < fluxos.paginacao.tamanho_pagina:
            raise ErroCompatibilidadeConfiguracao(
                "O tamanho de lote do staging deve ser maior ou igual ao tamanho de página."
            )

    def _validar_coerencia_staging(self) -> None:
        staging = self._configuracoes.staging.staging
        tecnologias_permitidas = ("sqlite", "postgres")
        if staging.tecnologia not in tecnologias_permitidas:
            raise ErroCompatibilidadeConfiguracao(
                f"Tecnologia de staging '{staging.tecnologia}' não suportada. Opções: {tecnologias_permitidas}"
            )
        if staging.tecnologia == "sqlite" and not staging.conexao.sqlite.caminho:
            raise ErroCompatibilidadeConfiguracao(
                "Caminho do banco SQLite não pode ser vazio."
            )

    def _validar_parametros_steam(self) -> None:
        steam = self._configuracoes.steam.steam
        if not steam.jogos:
            raise ErroCompatibilidadeConfiguracao(
                "A lista de jogos para coleta da Steam não pode estar vazia."
            )
        for jogo in steam.jogos:
            if jogo.appid <= 0:
                raise ErroCompatibilidadeConfiguracao(
                    f"AppID inválido para jogo da Steam: {jogo.appid}"
                )
