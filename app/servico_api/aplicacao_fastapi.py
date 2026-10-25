"""Aplicação FastAPI para auditoria de negócio, métricas e inferência controlada."""

from fastapi import FastAPI, HTTPException, Query, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, ConfigDict, Field


class RespostaSaude(BaseModel):
    """Modelo de resposta para o endpoint de healthcheck."""

    model_config = ConfigDict(extra="forbid")
    status: str
    servico: str
    versao: str


class SolicitacaoPredicao(BaseModel):
    """Payload de entrada para inferência de novos pontos tabulares."""

    model_config = ConfigDict(extra="forbid")
    dados_atributos: list[list[float]] = Field(
        ...,
        description="Lista de vetores numéricos com atributos num_reviews, playtime, etc.",
    )


class RespostaPredicao(BaseModel):
    """Resultado da inferência de partição de clusters."""

    model_config = ConfigDict(extra="forbid")
    appid: int
    clusters_atribuidos: list[int]


class ItemReviewConsulta(BaseModel):
    """Estrutura analítica de avaliação preservada para auditoria humana sem PLN."""

    model_config = ConfigDict(extra="forbid")
    recommendationid: str
    cluster_id: int
    voted_up: bool
    playtime_forever: int
    review_texto: str


class RespostaConsultaReviews(BaseModel):
    """Resultado paginado da consulta humana de reviews por cluster."""

    model_config = ConfigDict(extra="forbid")
    appid: int
    total_retornado: int
    reviews: list[ItemReviewConsulta]


class RespostaInfoClusters(BaseModel):
    """Metadados e configuração da partição analítica do jogo."""

    model_config = ConfigDict(extra="forbid")
    appid: int
    total_clusters: int
    algoritmo: str
    status: str


def criar_aplicacao() -> FastAPI:
    """Fábrica oficial que constrói e configura a instância da aplicação FastAPI."""
    app = FastAPI(
        title="Steam Reviews Clustering API",
        version="4.1.0",
        description="API REST para consulta analítica de clusters, recuperação de reviews e métricas Prometheus.",
    )

    @app.get("/health", response_model=RespostaSaude, tags=["Operacional"])
    def verificar_saude() -> RespostaSaude:
        """Endpoint de prontidão e verificação de integridade operacional."""
        return RespostaSaude(
            status="healthy",
            servico="steam-reviews-clustering",
            versao="4.1",
        )

    @app.get("/metrics", tags=["Observabilidade"])
    def obter_metricas_prometheus() -> Response:
        """Exporta métricas operacionais e analíticas formatadas para o Prometheus."""
        conteudo = generate_latest()
        return Response(content=conteudo, media_type=CONTENT_TYPE_LATEST)

    @app.get(
        "/api/v1/jogos/{appid}/clusters",
        response_model=RespostaInfoClusters,
        tags=["Analítica"],
    )
    def obter_info_clusters(appid: int) -> RespostaInfoClusters:
        """Retorna sumário estruturado dos clusters identificados para o jogo."""
        if appid <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O AppID informado deve ser um número inteiro positivo.",
            )
        return RespostaInfoClusters(
            appid=appid,
            total_clusters=3,
            algoritmo="kmeans",
            status="ativo",
        )

    @app.get(
        "/api/v1/jogos/{appid}/reviews",
        response_model=RespostaConsultaReviews,
        tags=["Consulta Humana"],
    )
    def consultar_reviews_cluster(
        appid: int,
        cluster_id: int | None = Query(
            default=None, description="Filtro opcional por cluster"
        ),
        limite: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> RespostaConsultaReviews:
        """Recupera avaliações textuais originais para leitura humana sem inferência de PLN."""
        if appid <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AppID inválido.",
            )

        # Exemplo determinístico de recuperação de reviews para inspeção por analista
        amostras = [
            ItemReviewConsulta(
                recommendationid="1001",
                cluster_id=0,
                voted_up=True,
                playtime_forever=15000,
                review_texto="Jogo excelente para veteranos, centenas de horas de diversão.",
            ),
            ItemReviewConsulta(
                recommendationid="1002",
                cluster_id=1,
                voted_up=False,
                playtime_forever=120,
                review_texto="Muitos bugs no início, não recomendo para novatos.",
            ),
        ]

        if cluster_id is not None:
            amostras = [r for r in amostras if r.cluster_id == cluster_id]

        fatia = amostras[offset : offset + limite]
        return RespostaConsultaReviews(
            appid=appid,
            total_retornado=len(fatia),
            reviews=fatia,
        )

    @app.post(
        "/api/v1/jogos/{appid}/predizer",
        response_model=RespostaPredicao,
        tags=["Inferência"],
    )
    def predizer_clusters(appid: int, payload: SolicitacaoPredicao) -> RespostaPredicao:
        """Atribui clusters a novos pontos com validação das capacidades do modelo."""
        if not payload.dados_atributos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A lista de vetores de atributos não pode estar vazia.",
            )

        # Mapeamento determinístico simples para inferência de teste
        clusters_calculados = [int(sum(v)) % 3 for v in payload.dados_atributos]
        return RespostaPredicao(
            appid=appid,
            clusters_atribuidos=clusters_calculados,
        )

    return app
