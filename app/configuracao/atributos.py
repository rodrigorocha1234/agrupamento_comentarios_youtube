"""Modelos de especificação de atributos de treino, avaliação e engenharia."""

from pydantic import BaseModel, Field


class ConfigTreinoAtributos(BaseModel):
    habilitado: bool = True
    colunas: list[str] = Field(default_factory=list)


class ConfigAvaliacaoAtributos(BaseModel):
    colunas: list[str] = Field(default_factory=list)


class ConfigEngenhariaAtributos(BaseModel):
    habilitado: bool = False
    operacoes: list[dict[str, str | int | float | bool]] = Field(default_factory=list)


class ConfigTextoAtributos(BaseModel):
    incluir_no_treino: bool = False
    motivo: str = ""


class ConfigAtributosInfo(BaseModel):
    identificadores: list[str] = Field(default_factory=list)
    treino: ConfigTreinoAtributos = Field(default_factory=ConfigTreinoAtributos)
    avaliacao: ConfigAvaliacaoAtributos = Field(default_factory=ConfigAvaliacaoAtributos)
    engenharia: ConfigEngenhariaAtributos = Field(default_factory=ConfigEngenhariaAtributos)
    texto: ConfigTextoAtributos = Field(default_factory=ConfigTextoAtributos)


class ConfigAtributos(BaseModel):
    atributos: ConfigAtributosInfo = Field(default_factory=ConfigAtributosInfo)
