"""Modelos de observabilidade técnica e analítica (Prometheus, Grafana, Loki)."""

from pydantic import BaseModel, Field


class ConfigPrometheus(BaseModel):
    habilitado: bool = True
    caminho_metricas: str = "/metrics"


class ConfigGrafana(BaseModel):
    habilitado: bool = True
    dashboards: list[str] = Field(default_factory=list)


class ConfigLogsObservabilidade(BaseModel):
    engine: str = "loki"
    alloy_habilitado: bool = True


class ConfigMetricasObservabilidade(BaseModel):
    latencia_percentis: list[float] = Field(default_factory=lambda: [0.50, 0.95, 0.99])
    coletar_throughput: bool = True
    coletar_erros: bool = True
    coletar_retries: bool = True
    coletar_freshness: bool = True
    coletar_qualidade_dados: bool = True


class ConfigObservabilidadeInfo(BaseModel):
    prometheus: ConfigPrometheus = Field(default_factory=ConfigPrometheus)
    grafana: ConfigGrafana = Field(default_factory=ConfigGrafana)
    logs: ConfigLogsObservabilidade = Field(default_factory=ConfigLogsObservabilidade)
    metricas: ConfigMetricasObservabilidade = Field(default_factory=ConfigMetricasObservabilidade)


class ConfigObservabilidade(BaseModel):
    observabilidade: ConfigObservabilidadeInfo = Field(default_factory=ConfigObservabilidadeInfo)
