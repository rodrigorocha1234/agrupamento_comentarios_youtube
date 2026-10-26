"""Modelos de configuração da API REST FastAPI."""

from pydantic import BaseModel, Field


class ConfigEndpointsAPI(BaseModel):
    health: str = "/health"
    ready: str = "/ready"
    metrics: str = "/metrics"
    model: str = "/model"
    clusters: str = "/clusters"
    predict: str = "/predict"
    predict_batch: str = "/predict-batch"


class ConfigLimitesAPI(BaseModel):
    tamanho_lote_maximo: int = 1000


class ConfigPrevisaoAPI(BaseModel):
    exigir_suporte_do_algoritmo: bool = True


class ConfigAPIInfo(BaseModel):
    habilitado: bool = True
    prefixo: str = "/api/v1"
    endpoints: ConfigEndpointsAPI = Field(default_factory=ConfigEndpointsAPI)
    limites: ConfigLimitesAPI = Field(default_factory=ConfigLimitesAPI)
    previsao: ConfigPrevisaoAPI = Field(default_factory=ConfigPrevisaoAPI)


class ConfigAPI(BaseModel):
    api: ConfigAPIInfo = Field(default_factory=ConfigAPIInfo)
