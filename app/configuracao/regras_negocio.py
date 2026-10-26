"""Modelos de configuração do motor declarativo de regras de negócio."""

from typing import Literal

from pydantic import BaseModel, Field


class ConfigCondicaoRegra(BaseModel):
    atributo: str = ""
    metrica: Literal["valor", "media", "mediana", "min", "max"] = "valor"
    operador: Literal[">", ">=", "<", "<=", "==", "!="] = ">="
    valor: float | int | str | bool = ""
    expressao_pandas: str = ""
    expressao_polars: str = ""


class ConfigAcaoRegra(BaseModel):
    rotulo: str = ""
    alerta: bool = False
    prioridade: Literal["baixa", "media", "alta", "critica"] = "media"
    tag: str = ""


class ConfigRegraItem(BaseModel):
    nome: str
    descricao: str = ""
    habilitado: bool = True
    alvo: Literal["cluster", "amostra"] = "cluster"
    expressao_pandas: str = ""
    expressao_polars: str = ""
    acao: ConfigAcaoRegra = Field(default_factory=ConfigAcaoRegra)


class ConfigRegrasNegocioInfo(BaseModel):
    habilitado: bool = False
    motor: Literal["pandas", "polars"] = "pandas"
    regras: list[ConfigRegraItem] = Field(default_factory=list)


class ConfigRegrasNegocio(BaseModel):
    regras_negocio: ConfigRegrasNegocioInfo = Field(default_factory=ConfigRegrasNegocioInfo)
