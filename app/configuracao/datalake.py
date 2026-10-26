"""Modelos de configuração do Data Lakehouse (S3 / RustFS)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConfigCamadaLake(BaseModel):
    prefixo: str = "bronze"
    caminho: str | None = None

    @model_validator(mode="after")
    def resolver_prefixo(self) -> "ConfigCamadaLake":
        if self.caminho and (not self.prefixo or self.prefixo == "bronze"):
            self.prefixo = self.caminho.strip("/").split("/")[-1]
        return self


class ConfigMetadadosLake(BaseModel):
    model_config = ConfigDict(extra="allow")
    incluir_timestamp_coleta: bool = True
    incluir_identificador: bool = True
    incluir_appid: bool | None = None
    incluir_versao_schema: bool = True

    @model_validator(mode="after")
    def sincronizar_identificador(self) -> "ConfigMetadadosLake":
        if self.incluir_appid is not None:
            self.incluir_identificador = self.incluir_appid
        return self


class ConfigDatalakeInfo(BaseModel):
    habilitado: bool = True
    tipo: Literal["s3", "rustfs"] = "s3"
    formato: Literal["parquet", "json"] = "parquet"
    bucket: str = "datalake-clustering"
    endpoint_url: str = "http://127.0.0.1:9000"
    regiao: str = "us-east-1"
    caminho: str | None = None
    caminho_base: str | None = None
    bronze: ConfigCamadaLake = Field(default_factory=lambda: ConfigCamadaLake(prefixo="bronze"))
    silver: ConfigCamadaLake = Field(default_factory=lambda: ConfigCamadaLake(prefixo="silver"))
    gold: ConfigCamadaLake = Field(default_factory=lambda: ConfigCamadaLake(prefixo="gold"))
    metadados: ConfigMetadadosLake = Field(default_factory=ConfigMetadadosLake)

    @model_validator(mode="after")
    def resolver_caminho_geral(self) -> "ConfigDatalakeInfo":
        if self.caminho and not self.caminho_base:
            self.caminho_base = self.caminho
        elif self.caminho_base and not self.caminho:
            self.caminho = self.caminho_base
        return self


class ConfigDatalake(BaseModel):
    datalake: ConfigDatalakeInfo = Field(default_factory=ConfigDatalakeInfo)
