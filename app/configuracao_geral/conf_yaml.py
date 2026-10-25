"""Fachada exclusiva de carregamento, validação e versionamento de configurações declarativas YAML."""

import hashlib
import os
import re
from pathlib import Path
from typing import Final, cast, final

import yaml

from app.configuracao_geral.modelos_configuracao import (
    ConfiguracaoDatalake,
    ConfiguracaoFluxosIncrementais,
    ConfiguracaoMlflow,
    ConfiguracaoNegocio,
    ConfiguracaoProjeto,
    ConfiguracaoStaging,
    ConfiguracaoSteamApi,
)
from app.dominio_contratos.modelos_dados import TipoDadoJson


@final
class ConfYAML:
    """Fachada única e imutável para carregamento e validação de configurações."""

    _PADRAO_VARIAVEL_AMBIENTE: Final[re.Pattern[str]] = re.compile(
        r"\$\{(?P<nome>[A-Z0-9_]+)(?::-(?P<padrao>[^\}]*))?\}"
    )

    def __init__(self, diretorio_base: Path | str = "configuracoes") -> None:
        self._diretorio: Final[Path] = Path(diretorio_base).resolve()
        if not self._diretorio.exists() or not self._diretorio.is_dir():
            raise FileNotFoundError(
                f"Diretório de configurações não encontrado: {self._diretorio}"
            )

        self._projeto: Final[ConfiguracaoProjeto] = self._carregar_projeto()
        self._steam: Final[ConfiguracaoSteamApi] = self._carregar_steam()
        self._staging: Final[ConfiguracaoStaging] = self._carregar_staging()
        self._datalake: Final[ConfiguracaoDatalake] = self._carregar_datalake()
        self._mlflow: Final[ConfiguracaoMlflow] = self._carregar_mlflow()
        self._fluxos: Final[ConfiguracaoFluxosIncrementais] = self._carregar_fluxos()
        self._negocio: Final[ConfiguracaoNegocio] = self._carregar_negocio()
        self._hash_configuracao: Final[str] = self._calcular_hash_arquivos()

    @property
    def projeto(self) -> ConfiguracaoProjeto:
        """Retorna a configuração geral do projeto."""
        return self._projeto

    @property
    def steam(self) -> ConfiguracaoSteamApi:
        """Retorna as configurações do serviço da Steam."""
        return self._steam

    @property
    def staging(self) -> ConfiguracaoStaging:
        """Retorna as definições do banco de staging."""
        return self._staging

    @property
    def datalake(self) -> ConfiguracaoDatalake:
        """Retorna as configurações do Lakehouse."""
        return self._datalake

    @property
    def mlflow(self) -> ConfiguracaoMlflow:
        """Retorna as configurações de tracking do MLflow."""
        return self._mlflow

    @property
    def fluxos_incrementais(self) -> ConfiguracaoFluxosIncrementais:
        """Retorna os parâmetros de paginação e streaming incremental."""
        return self._fluxos

    @property
    def negocio(self) -> ConfiguracaoNegocio:
        """Retorna as definições de regras declarativas de negócio."""
        return self._negocio

    @property
    def hash_configuracao(self) -> str:
        """Hash criptográfico SHA-256 do conjunto de arquivos de configuração."""
        return self._hash_configuracao

    def _interpolar_variaveis(self, conteudo_texto: str) -> str:
        """Substitui padrões ${VAR:-default} sem eval/exec."""

        def _substituidor(casamento: re.Match[str]) -> str:
            nome_var = casamento.group("nome")
            valor_padrao = casamento.group("padrao") or ""
            return os.getenv(nome_var, valor_padrao)

        return self._PADRAO_VARIAVEL_AMBIENTE.sub(_substituidor, conteudo_texto)

    def _ler_arquivo_yaml(self, caminho_relativo: str) -> dict[str, TipoDadoJson]:
        """Lê e analisa um arquivo YAML interpolando variáveis de ambiente."""
        caminho_completo = self._diretorio / caminho_relativo
        if not caminho_completo.exists():
            raise FileNotFoundError(
                f"Arquivo de configuração não localizado: {caminho_completo}"
            )

        conteudo_original = caminho_completo.read_text(encoding="utf-8")
        conteudo_interpolado = self._interpolar_variaveis(conteudo_original)
        dados_carregados = yaml.safe_load(conteudo_interpolado)

        if not isinstance(dados_carregados, dict):
            raise TypeError(
                f"O arquivo {caminho_relativo} deve conter um mapeamento YAML de primeiro nível."
            )

        # Garantir retorno tipado sem Any ou object
        resultado: dict[str, TipoDadoJson] = {}
        for chave, valor in dados_carregados.items():
            if isinstance(chave, str):
                resultado[chave] = cast(TipoDadoJson, valor)
        return resultado

    def _carregar_projeto(self) -> ConfiguracaoProjeto:
        dados = self._ler_arquivo_yaml("projeto.yaml")
        return ConfiguracaoProjeto.model_validate(dados)

    def _carregar_steam(self) -> ConfiguracaoSteamApi:
        dados = self._ler_arquivo_yaml("fontes/steam_api.yaml")
        return ConfiguracaoSteamApi.model_validate(dados)

    def _carregar_staging(self) -> ConfiguracaoStaging:
        dados = self._ler_arquivo_yaml("infraestrutura/staging.yaml")
        return ConfiguracaoStaging.model_validate(dados)

    def _carregar_datalake(self) -> ConfiguracaoDatalake:
        dados = self._ler_arquivo_yaml("infraestrutura/datalake.yaml")
        return ConfiguracaoDatalake.model_validate(dados)

    def _carregar_mlflow(self) -> ConfiguracaoMlflow:
        dados = self._ler_arquivo_yaml("infraestrutura/mlflow.yaml")
        return ConfiguracaoMlflow.model_validate(dados)

    def _carregar_fluxos(self) -> ConfiguracaoFluxosIncrementais:
        dados = self._ler_arquivo_yaml("processamento/fluxos_incrementais.yaml")
        return ConfiguracaoFluxosIncrementais.model_validate(dados)

    def _carregar_negocio(self) -> ConfiguracaoNegocio:
        dados = self._ler_arquivo_yaml("analises/negocio.yaml")
        return ConfiguracaoNegocio.model_validate(dados)

    def _calcular_hash_arquivos(self) -> str:
        """Calcula o digest SHA-256 combinando todos os arquivos YAML ordenados."""
        arquivos = sorted(self._diretorio.glob("**/*.yaml"))
        hasher = hashlib.sha256()
        for arquivo in arquivos:
            hasher.update(arquivo.name.encode("utf-8"))
            hasher.update(arquivo.read_bytes())
        return hasher.hexdigest()
