"""Modelos de algoritmos de clustering e estratégias de ajuste."""

from typing import Literal

from pydantic import BaseModel, Field


class ConfigParametrosKMeans(BaseModel):
    n_clusters: int = 5
    init: str = "k-means++"
    n_init: str | int = "auto"
    max_iter: int = 300


class ConfigParametrosDBSCAN(BaseModel):
    eps: float = 0.5
    min_samples: int = 5
    metric: str = "euclidean"


class ConfigParametrosHDBSCAN(BaseModel):
    min_cluster_size: int = 15
    min_samples: int | None = None
    metric: str = "euclidean"


class ConfigAlgoritmosClustering(BaseModel):
    kmeans: ConfigParametrosKMeans = Field(default_factory=ConfigParametrosKMeans)
    dbscan: ConfigParametrosDBSCAN = Field(default_factory=ConfigParametrosDBSCAN)
    hdbscan: ConfigParametrosHDBSCAN = Field(default_factory=ConfigParametrosHDBSCAN)


class ConfigTuningClustering(BaseModel):
    habilitado: bool = False
    estrategia: str = "grid"
    parametros: dict[str, list[int | float | str]] = Field(default_factory=dict)


class ConfigReproducibilidadeClustering(BaseModel):
    registrar_versoes: bool = True
    registrar_configuracao: bool = True


class ConfigClusteringInfo(BaseModel):
    motor: Literal["sklearn", "pycaret"] = "sklearn"
    algoritmo: Literal["kmeans", "dbscan", "hdbscan"] = "kmeans"
    random_state: int = 42
    algoritmos: ConfigAlgoritmosClustering = Field(default_factory=ConfigAlgoritmosClustering)
    tuning: ConfigTuningClustering = Field(default_factory=ConfigTuningClustering)
    reproducibilidade: ConfigReproducibilidadeClustering = Field(default_factory=ConfigReproducibilidadeClustering)


class ConfigClustering(BaseModel):
    clustering: ConfigClusteringInfo = Field(default_factory=ConfigClusteringInfo)
