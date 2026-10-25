"""Estado em memória compartilhado para injeção de dependências na API FastAPI."""

from dataclasses import dataclass, field

from app.analise_clusters.analisador_clusters import ResumoAnaliseClusters
from app.conf_yaml import ConfigAPIInfo, ConfigClusteringInfo
from app.contratos.motor_clustering import ProtocoloMotorClustering
from app.contratos.repositorio import ProtocoloRepositorioLakehouse


@dataclass
class EstadoAplicacao:
    """Encapsula componentes ativos (modelo, lakehouse, perfis) para rotas da API."""

    config_api: ConfigAPIInfo = field(default_factory=ConfigAPIInfo)
    config_clustering: ConfigClusteringInfo = field(default_factory=ConfigClusteringInfo)
    motor: ProtocoloMotorClustering | None = None
    repositorio: ProtocoloRepositorioLakehouse | None = None
    resumo_clusters: ResumoAnaliseClusters | None = None
    nomes_atributos: list[str] = field(default_factory=list)
