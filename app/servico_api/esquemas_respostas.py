"""Modelos Pydantic tipados estritos para requisições e respostas da API REST."""

from typing import Self
from pydantic import BaseModel, Field, model_validator

from app.configuracao_geral.tipos_enumerados import (
    JanelaTemporal,
    StatusTendencia,
    TecnicaCluster,
)


MAPA_METADADOS_TECNICAS: dict[str, tuple[str, str]] = {
    "kmeans": (
        "Panorama Geral (Macro Temas)",
        "Distribuição proporcional de 100% dos comentários em macro temas globais do canal.",
    ),
    "dbscan": (
        "Assuntos em Alta & Nichos Emergentes",
        "Detecção de nichos específicos e termos emergentes de alta densidade, isolando mensagens avulsas.",
    ),
    "hdbscan": (
        "Consenso & Alta Confiança",
        "Identificação de núcleos temáticos persistentes com alto consenso da comunidade.",
    ),
}


def obter_metadados_tecnica(tecnica: str) -> tuple[str, str]:
    """Retorna nome amigável de produto e a descrição de lente analítica para uma técnica de clustering."""
    chave = str(tecnica).lower().strip()
    return MAPA_METADADOS_TECNICAS.get(
        chave,
        (
            f"Análise Temática ({tecnica})",
            "Classificação e agrupamento temático não-supervisionado de comentários.",
        ),
    )


class RespostaTopicoItem(BaseModel):
    """Representação de um tópico individual na resposta de tendências."""

    topico: str
    contagem_atual: int
    contagem_anterior: int
    variacao_proporcao: float
    status_tendencia: StatusTendencia | str
    comentarios: list[str] = Field(default_factory=list, description="Lista de todos os comentários associados ao tópico")
    percentual_variacao: float = 0.0
    data_referencia: str = ""

    @model_validator(mode="before")
    @classmethod
    def compatibilidade_comentarios(cls, data: object) -> object:
        """Permite inicialização tanto com 'comentarios' quanto com 'comentarios_amostra'."""
        if isinstance(data, dict):
            if "comentarios" not in data and "comentarios_amostra" in data:
                data["comentarios"] = data["comentarios_amostra"]
        return data


class RespostaTendenciasCanal(BaseModel):
    """Resposta com tendências agregadas de um canal."""

    id_canal: str
    tecnica: TecnicaCluster | str
    nome_amigavel_tecnica: str = Field(default="", description="Nome amigável da técnica orientado a negócios")
    descricao_lente: str = Field(default="", description="Descrição da lente de visualização analítica para o cliente")
    topicos: list[RespostaTopicoItem]
    data_referencia: str = ""
    janela: JanelaTemporal | str = ""

    @model_validator(mode="after")
    def _preencher_metadados_tecnica(self) -> Self:
        if not self.nome_amigavel_tecnica:
            nome, desc = obter_metadados_tecnica(str(self.tecnica))
            self.nome_amigavel_tecnica = nome
            self.descricao_lente = desc
        return self


class ItemVideoCatalogo(BaseModel):
    """Representação de um vídeo individual no catálogo do canal."""

    id_video: str
    nome_video: str


class RespostaCatalogoVideosCanal(BaseModel):
    """Resposta listando o nome do canal e seus vídeos associados."""

    id_canal: str
    nome_canal: str
    total_videos: int
    videos: list[ItemVideoCatalogo]


class RespostaPontoSerieTemporal(BaseModel):
    """Ponto de dados de uma série temporal diária para um tópico."""

    data: str
    contagem: int
    percentual_variacao: float
    status_tendencia: StatusTendencia | str


class RespostaSerieTemporalTopico(BaseModel):
    """Série temporal histórica de um tópico específico ao longo dos dias."""

    id_canal: str
    topico: str
    tecnica: TecnicaCluster | str
    nome_amigavel_tecnica: str = Field(default="", description="Nome amigável da técnica orientado a negócios")
    descricao_lente: str = Field(default="", description="Descrição da lente de visualização analítica para o cliente")
    pontos: list[RespostaPontoSerieTemporal]

    @model_validator(mode="after")
    def _preencher_metadados_tecnica(self) -> Self:
        if not self.nome_amigavel_tecnica:
            nome, desc = obter_metadados_tecnica(str(self.tecnica))
            self.nome_amigavel_tecnica = nome
            self.descricao_lente = desc
        return self


class RespostaTendenciasVideo(BaseModel):
    """Resposta com tendências específicas de um vídeo."""

    id_canal: str
    id_video: str
    tecnica: TecnicaCluster | str
    nome_amigavel_tecnica: str = Field(default="", description="Nome amigável da técnica orientado a negócios")
    descricao_lente: str = Field(default="", description="Descrição da lente de visualização analítica para o cliente")
    topicos: list[RespostaTopicoItem]
    data_referencia: str = ""
    janela: JanelaTemporal | str = ""

    @model_validator(mode="after")
    def _preencher_metadados_tecnica(self) -> Self:
        if not self.nome_amigavel_tecnica:
            nome, desc = obter_metadados_tecnica(str(self.tecnica))
            self.nome_amigavel_tecnica = nome
            self.descricao_lente = desc
        return self


class RespostaEstatisticaCluster(BaseModel):
    """Resumo estatístico de um cluster identificado."""

    cluster_id: int
    rotulo_topico: str
    total_comentarios: int
    percentual_total: float


class RespostaClustersVideo(BaseModel):
    """Resposta com informações de clusterização de um vídeo."""

    id_canal: str
    id_video: str
    tecnica: TecnicaCluster | str
    nome_amigavel_tecnica: str = Field(default="", description="Nome amigável da técnica orientado a negócios")
    descricao_lente: str = Field(default="", description="Descrição da lente de visualização analítica para o cliente")
    quantidade_clusters: int
    fracao_ruido: float
    clusters: list[RespostaEstatisticaCluster]

    @model_validator(mode="after")
    def _preencher_metadados_tecnica(self) -> Self:
        if not self.nome_amigavel_tecnica:
            nome, desc = obter_metadados_tecnica(str(self.tecnica))
            self.nome_amigavel_tecnica = nome
            self.descricao_lente = desc
        return self


class RespostaComentariosTopico(BaseModel):
    """Resposta paginada de comentários vinculados a um tópico."""

    id_canal: str
    id_video: str | None = None
    topico: str
    tecnica: TecnicaCluster | str
    nome_amigavel_tecnica: str = Field(default="", description="Nome amigável da técnica orientado a negócios")
    descricao_lente: str = Field(default="", description="Descrição da lente de visualização analítica para o cliente")
    pagina: int
    total_amostras: int
    comentarios: list[str]

    @model_validator(mode="after")
    def _preencher_metadados_tecnica(self) -> Self:
        if not self.nome_amigavel_tecnica:
            nome, desc = obter_metadados_tecnica(str(self.tecnica))
            self.nome_amigavel_tecnica = nome
            self.descricao_lente = desc
        return self


class RequisicaoInferencia(BaseModel):
    """Payload de entrada para inferência de cluster via serving."""

    textos: list[str] = Field(..., min_length=1)


class RespostaInferencia(BaseModel):
    """Resultado da inferência retornado pelo serving do modelo."""

    predicoes: list[int]
    total_amostras: int


class TermoCentroide(BaseModel):
    """Termo individual representativo e seu peso médio no centróide."""

    termo: str
    peso: float


class DetalheCentroide(BaseModel):
    """Detalhamento semântico do centróide de um cluster."""

    cluster_id: int
    rotulo_topico: str
    total_comentarios: int
    top_termos: list[TermoCentroide]
    comentario_exemplar: str | None = None


class RespostaCentroidesVideo(BaseModel):
    """Resposta com os centróides e coordenadas semânticas dos clusters de um vídeo."""

    id_canal: str
    id_video: str
    tecnica: TecnicaCluster | str
    nome_amigavel_tecnica: str = Field(default="", description="Nome amigável da técnica orientado a negócios")
    descricao_lente: str = Field(default="", description="Descrição da lente de visualização analítica para o cliente")
    total_clusters: int
    centroides: list[DetalheCentroide]
    janela: JanelaTemporal | str = ""

    @model_validator(mode="after")
    def _preencher_metadados_tecnica(self) -> Self:
        if not self.nome_amigavel_tecnica:
            nome, desc = obter_metadados_tecnica(str(self.tecnica))
            self.nome_amigavel_tecnica = nome
            self.descricao_lente = desc
        return self


class RespostaCentroidesCanal(BaseModel):
    """Resposta com os centróides e coordenadas semânticas dos clusters de um canal ou vídeo filtrado."""

    id_canal: str
    id_video: str | None = None
    tecnica: TecnicaCluster | str
    nome_amigavel_tecnica: str = Field(default="", description="Nome amigável da técnica orientado a negócios")
    descricao_lente: str = Field(default="", description="Descrição da lente de visualização analítica para o cliente")
    total_clusters: int
    centroides: list[DetalheCentroide]
    janela: JanelaTemporal | str = ""

    @model_validator(mode="after")
    def _preencher_metadados_tecnica(self) -> Self:
        if not self.nome_amigavel_tecnica:
            nome, desc = obter_metadados_tecnica(str(self.tecnica))
            self.nome_amigavel_tecnica = nome
            self.descricao_lente = desc
        return self


