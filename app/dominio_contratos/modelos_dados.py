"""Entidades de domínio imutáveis e fortemente tipadas para o projeto Steam Reviews."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

type TipoValorEscalar = int | float | str | bool | None
type TipoParametroSql = int | float | str | bool | bytes | datetime | None
type TipoParametroAlgoritmo = int | float | str | bool | None
type TipoDadoJson = (
    int
    | float
    | str
    | bool
    | None
    | Sequence["TipoDadoJson"]
    | Mapping[str, "TipoDadoJson"]
)


@dataclass(frozen=True, slots=True)
class AutorSteam:
    """Dados cadastrais e métricas públicas de jogo do autor na Steam."""

    steamid: str
    num_games_owned: int
    num_reviews: int
    playtime_forever: int
    playtime_last_two_weeks: int
    playtime_at_review: int
    last_played: int


@dataclass(frozen=True, slots=True)
class ReviewSteam:
    """Avaliação pública individual de um jogo na Steam."""

    appid: int
    recommendationid: str
    author: AutorSteam
    language: str
    review_texto: str  # Preservado exclusivamente para auditoria e consulta humana
    timestamp_created: int
    timestamp_updated: int
    voted_up: bool
    votes_up: int
    votes_funny: int
    weighted_vote_score: float
    comment_count: int
    steam_purchase: bool
    received_for_free: bool
    written_during_early_access: bool
    primarily_steam_deck: bool
    developer_response: str | None = None


@dataclass(frozen=True, slots=True)
class PaginaReviews:
    """Página de avaliações retornada pela API e transmitida pelo gerador lazy."""

    appid: int
    reviews: tuple[ReviewSteam, ...]
    cursor_entrada: str
    cursor_proximo: str | None
    total_reviews_pagina: int
    hash_payload: str
    momento_coleta: datetime


@dataclass(frozen=True, slots=True)
class MetadadosExecucao:
    """Informações de auditoria e linhagem de uma sessão de coleta."""

    id_execucao: str
    appid: int
    estrategia: str
    data_inicio: datetime
    data_fim: datetime | None
    status: str
    total_paginas: int
    total_reviews: int
    mensagem_erro: str | None = None


@dataclass(frozen=True, slots=True)
class EventoPublicacao:
    """Evento da tabela outbox para entrega desacoplada e idempotente ao Data Lake."""

    id_evento: str
    tipo_evento: str  # ex: "bronze_pagina", "silver_reviews"
    chave_origem: str  # ex: appid:recommendationid ou appid:cursor
    payload_referencia: str
    status_publicacao: str  # "pendente", "publicado", "falhou"
    tentativas: int
    data_criacao: datetime
    data_publicacao: datetime | None = None
