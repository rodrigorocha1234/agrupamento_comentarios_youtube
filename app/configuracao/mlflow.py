"""Modelos de rastreamento de experimentos com MLflow Tracking Server."""

from pydantic import BaseModel, Field


class ConfigMLflowInfo(BaseModel):
    habilitado: bool = True
    tracking_uri: str = "http://localhost:5000"
    experiment_name: str = "experimento_clustering"
    registrar_parametros: bool = True
    registrar_metricas: bool = True
    registrar_modelo: bool = True
    registrar_artefatos: bool = True
    tags: dict[str, str] = Field(default_factory=dict)


class ConfigMLflow(BaseModel):
    mlflow: ConfigMLflowInfo = Field(default_factory=ConfigMLflowInfo)
