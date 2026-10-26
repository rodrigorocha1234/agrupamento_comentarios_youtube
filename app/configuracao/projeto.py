"""Modelos de configuração global do projeto e chaves de funcionalidades."""

from pydantic import BaseModel, Field


class ConfigProjetoInfo(BaseModel):
    nome: str = "projeto_clustering"
    ambiente: str = "desenvolvimento"
    idioma: str = "pt-BR"


class ConfigFuncionalidadePLN(BaseModel):
    habilitado: bool = False


class ConfigFuncionalidadeTemporal(BaseModel):
    habilitado: bool = False


class ConfigFuncionalidadeAPI(BaseModel):
    habilitado: bool = True


class ConfigFuncionalidadeMLflow(BaseModel):
    habilitado: bool = True


class ConfigFuncionalidades(BaseModel):
    pln: ConfigFuncionalidadePLN = Field(default_factory=ConfigFuncionalidadePLN)
    analise_temporal: ConfigFuncionalidadeTemporal = Field(default_factory=ConfigFuncionalidadeTemporal)
    api: ConfigFuncionalidadeAPI = Field(default_factory=ConfigFuncionalidadeAPI)
    mlflow: ConfigFuncionalidadeMLflow = Field(default_factory=ConfigFuncionalidadeMLflow)


class ConfigExecucao(BaseModel):
    modo: str = "incremental"
    falhar_em_configuracao_invalida: bool = True


class ConfigProjeto(BaseModel):
    projeto: ConfigProjetoInfo = Field(default_factory=ConfigProjetoInfo)
    funcionalidades: ConfigFuncionalidades = Field(default_factory=ConfigFuncionalidades)
    execucao: ConfigExecucao = Field(default_factory=ConfigExecucao)
