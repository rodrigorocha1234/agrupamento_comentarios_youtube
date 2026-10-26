"""Contratos, dataclasses imutáveis e estruturas de dados para análise temporal."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PontoTemporalCluster:
    """Representa as métricas de um cluster específico em uma fatia temporal."""

    periodo: str
    id_cluster: int
    nome_rotulo: str
    quantidade_amostras: int
    proporcao_periodo: float
    taxa_recomendacao: float | None = None
    media_horas_jogadas: float | None = None


@dataclass(frozen=True)
class AlertaPicoTemporal:
    """Registra uma anomalia estatística ou pico incomum de volume/sentimento."""

    periodo: str
    id_cluster: int
    nome_rotulo: str
    tipo_alerta: str
    z_score: float
    valor_observado: float
    media_historica: float
    descricao: str


@dataclass(frozen=True)
class ResumoAnaliseTemporal:
    """Consolidado analítico da dinâmica temporal de todos os clusters."""

    pontos_temporais: list[PontoTemporalCluster]
    periodos_ordenados: list[str]
    clusters_presentes: list[int]
    alertas_picos: list[AlertaPicoTemporal] = field(default_factory=list)
    granularidade: str = "mensal"
    coluna_temporal: str = "timestamp_created"
    total_amostras_temporais: int = 0
