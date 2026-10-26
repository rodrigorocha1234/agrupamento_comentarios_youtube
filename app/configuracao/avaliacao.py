"""Modelos de avaliação intrínseca e métricas estatísticas dos agrupamentos."""

from pydantic import BaseModel, Field


class ConfigItemMetrica(BaseModel):
    habilitado: bool = True


class ConfigMetricasAvaliacao(BaseModel):
    silhouette: ConfigItemMetrica = Field(default_factory=ConfigItemMetrica)
    davies_bouldin: ConfigItemMetrica = Field(default_factory=ConfigItemMetrica)
    calinski_harabasz: ConfigItemMetrica = Field(default_factory=ConfigItemMetrica)
    proporcao_ruido: ConfigItemMetrica = Field(default_factory=ConfigItemMetrica)
    distribuicao_clusters: ConfigItemMetrica = Field(default_factory=ConfigItemMetrica)


class ConfigRestricoesAvaliacao(BaseModel):
    minimo_clusters_sem_ruido: int = 2
    permitir_cluster_unico: bool = False


class ConfigEstabilidadeAvaliacao(BaseModel):
    habilitado: bool = False
    repeticoes: int = 5


class ConfigAvaliacaoInfo(BaseModel):
    metricas: ConfigMetricasAvaliacao = Field(default_factory=ConfigMetricasAvaliacao)
    restricoes: ConfigRestricoesAvaliacao = Field(default_factory=ConfigRestricoesAvaliacao)
    estabilidade: ConfigEstabilidadeAvaliacao = Field(default_factory=ConfigEstabilidadeAvaliacao)


class ConfigAvaliacao(BaseModel):
    avaliacao: ConfigAvaliacaoInfo = Field(default_factory=ConfigAvaliacaoInfo)
