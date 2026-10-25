"""Modelos e esquemas de dados Pydantic para a API REST."""

from pydantic import BaseModel, Field


class RequisicaoPonto(BaseModel):
    """Payload contendo os valores dos atributos estruturados de uma amostra."""

    atributos: dict[str, float] = Field(
        ...,
        description="Mapeamento de nomes de atributos numéricos e seus respectivos valores.",
        examples=[{"voted_up": 1.0, "votes_up": 5.0, "author_playtime_forever": 320.0}],
    )


class RequisicaoLote(BaseModel):
    """Payload contendo lote de amostras para predição concorrente."""

    amostras: list[dict[str, float]] = Field(
        ...,
        description="Lista de dicionários de atributos.",
    )


class RespostaPrevisaoPonto(BaseModel):
    """Resposta com o cluster atribuído à amostra."""

    cluster_atribuido: int
    nome_rotulo: str
    algoritmo: str
    distancia_centroide: float | None = None


class RespostaPrevisaoLote(BaseModel):
    """Resposta com os clusters atribuídos ao lote."""

    clusters_atribuidos: list[int]
    total_amostras: int
    algoritmo: str


class RespostaSaude(BaseModel):
    """Status operacional do serviço."""

    status: str
    versao: str
    servicos: dict[str, str]


class RespostaProntidao(BaseModel):
    """Status de prontidão para receber tráfego de inferência."""

    pronto: bool
    datalake_acessivel: bool
    modelo_carregado: bool
    algoritmo_ativo: str | None = None
    detalhes: str = ""


class RespostaInfoModelo(BaseModel):
    """Metadados do modelo de agrupamento atualmente carregado."""

    modelo_carregado: bool
    algoritmo: str
    motor: str
    tem_centroides: bool
    suporta_previsao: bool
    quantidade_clusters: int
    nomes_atributos_esperados: list[str]


class RespostaPerfilCluster(BaseModel):
    """Perfil consolidado de um cluster."""

    id_cluster: int
    nome_rotulo: str
    quantidade_amostras: int
    proporcao_amostras: float
    medias_atributos: dict[str, float]
    medianas_atributos: dict[str, float]
    distancia_media_centroide: float | None = None
    rotulo_negocio: str | None = None
    alerta_negocio: bool = False
    prioridade_negocio: str | None = None
    metricas_personalizadas: dict[str, float] = Field(default_factory=dict)


class RespostaResumoClusters(BaseModel):
    """Sumário geral dos grupos formados pelo modelo."""

    algoritmo: str
    total_amostras: int
    quantidade_clusters_validos: int
    quantidade_ruido: int
    proporcao_ruido: float
    perfis: list[RespostaPerfilCluster]
