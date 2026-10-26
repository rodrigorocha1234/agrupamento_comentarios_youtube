"""Modelos de ingestão de fontes desacopladas (Steam, API REST, Banco de Dados)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConfigSegredoFonte(BaseModel):
    variavel_ambiente: str = ""


class ConfigBancoDadosInfo(BaseModel):
    dsn: str = ""
    consulta_ou_tabela: str = ""
    coluna_chave: str = "id"
    coluna_timestamp: str = "data_criacao"


class ConfigAPIRestInfo(BaseModel):
    endpoint: str = ""
    metodo: Literal["GET", "POST"] = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    parametro_paginacao: str = "cursor"


class ConfigFonteInfo(BaseModel):
    """Configuração genérica de fonte de dados."""

    tipo: Literal["steam_api", "banco_dados", "api_rest"] = "api_rest"
    endpoint: str | None = None
    timeout_segundos: int = 30
    tentativas_maximas: int = 5
    espera_base_segundos: float = 1.0
    identificadores: list[str | int] = Field(default_factory=list)
    appids: list[int] = Field(default_factory=list)
    segredo: ConfigSegredoFonte = Field(default_factory=ConfigSegredoFonte)
    banco_dados: ConfigBancoDadosInfo | None = None
    api_rest: ConfigAPIRestInfo | None = None

    @model_validator(mode="after")
    def sincronizar_identificadores(self) -> "ConfigFonteInfo":
        """Compatibiliza appids com o identificadores genérico."""
        if self.appids and not self.identificadores:
            self.identificadores = [str(x) for x in self.appids]
        elif self.identificadores and not self.appids:
            self.appids = [int(x) for x in self.identificadores if str(x).isdigit()]
        return self


class ConfigParametrosFonte(BaseModel):
    """Parâmetros arbitrários de consulta/requisição específicos da fonte informada no YAML."""

    model_config = ConfigDict(extra="allow")


class ConfigColeta(BaseModel):
    """Parâmetros de orquestração de coleta e checkpointing."""

    model_config = ConfigDict(extra="allow")
    incremental: bool = True
    checkpoint_habilitado: bool = True
    deduplicar_por: str = "id"
    intervalo_minutos: int = 1440


class ConfigFonteDados(BaseModel):
    fonte: ConfigFonteInfo = Field(default_factory=ConfigFonteInfo)
    parametros_api: ConfigParametrosFonte = Field(default_factory=ConfigParametrosFonte)
    coleta: ConfigColeta = Field(default_factory=ConfigColeta)
