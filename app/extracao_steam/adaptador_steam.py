"""Adaptador para converter payloads brutos da API Steam em modelos de domínio imutáveis."""

import hashlib
import json
from datetime import UTC, datetime
from typing import final

from app.dominio_contratos.modelos_dados import (
    AutorSteam,
    PaginaReviews,
    ReviewSteam,
    TipoDadoJson,
)


def _extrair_inteiro(valor: TipoDadoJson, padrao: int = 0) -> int:
    """Converte valor desconhecido para int de forma segura."""
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str) and valor.isdigit():
        return int(valor)
    return padrao


def _extrair_float(valor: TipoDadoJson, padrao: float = 0.0) -> float:
    """Converte valor desconhecido para float de forma segura."""
    if isinstance(valor, (float, int)):
        return float(valor)
    if isinstance(valor, str):
        try:
            return float(valor)
        except ValueError:
            return padrao
    return padrao


def _extrair_bool(valor: TipoDadoJson, padrao: bool = False) -> bool:
    """Converte valor desconhecido para bool de forma segura."""
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, int):
        return valor != 0
    return padrao


@final
class AdaptadorSteam:
    """Converte estruturas JSON da API GetAppReviews em modelos fortemente tipados."""

    def converter_pagina(
        self,
        appid: int,
        cursor_entrada: str,
        dados_brutos: dict[str, TipoDadoJson],
    ) -> PaginaReviews:
        """Converte o payload bruto em uma PaginaReviews tipada."""
        momento_atual = datetime.now(UTC)
        texto_serializado = json.dumps(dados_brutos, sort_keys=True)
        hash_payload = hashlib.sha256(texto_serializado.encode("utf-8")).hexdigest()

        cursor_proximo: str | None = None
        valor_cursor = dados_brutos.get("cursor")
        if isinstance(valor_cursor, str) and valor_cursor:
            cursor_proximo = valor_cursor

        lista_avaliacoes: list[ReviewSteam] = []
        avaliacoes_brutas = dados_brutos.get("reviews")
        if isinstance(avaliacoes_brutas, list):
            for item in avaliacoes_brutas:
                if isinstance(item, dict):
                    avaliacao = self._converter_avaliacao(appid, item)
                    if avaliacao is not None:
                        lista_avaliacoes.append(avaliacao)

        return PaginaReviews(
            appid=appid,
            reviews=tuple(lista_avaliacoes),
            cursor_entrada=cursor_entrada,
            cursor_proximo=cursor_proximo,
            total_reviews_pagina=len(lista_avaliacoes),
            hash_payload=hash_payload,
            momento_coleta=momento_atual,
        )

    def _converter_avaliacao(
        self, appid: int, dados_review: dict[str, TipoDadoJson]
    ) -> ReviewSteam | None:
        """Converte um item de review individual e seu autor."""
        rec_id = dados_review.get("recommendationid")
        if not rec_id:
            return None

        dados_autor = dados_review.get("author")
        if not isinstance(dados_autor, dict):
            return None

        autor = AutorSteam(
            steamid=str(dados_autor.get("steamid", "")),
            num_games_owned=_extrair_inteiro(dados_autor.get("num_games_owned")),
            num_reviews=_extrair_inteiro(dados_autor.get("num_reviews")),
            playtime_forever=_extrair_inteiro(dados_autor.get("playtime_forever")),
            playtime_last_two_weeks=_extrair_inteiro(
                dados_autor.get("playtime_last_two_weeks")
            ),
            playtime_at_review=_extrair_inteiro(dados_autor.get("playtime_at_review")),
            last_played=_extrair_inteiro(dados_autor.get("last_played")),
        )

        dev_resp = dados_review.get("developer_response")
        dev_resp_str: str | None = str(dev_resp) if isinstance(dev_resp, str) else None

        return ReviewSteam(
            appid=appid,
            recommendationid=str(rec_id),
            author=autor,
            language=str(dados_review.get("language", "")),
            review_texto=str(dados_review.get("review", "")),
            timestamp_created=_extrair_inteiro(dados_review.get("timestamp_created")),
            timestamp_updated=_extrair_inteiro(dados_review.get("timestamp_updated")),
            voted_up=_extrair_bool(dados_review.get("voted_up")),
            votes_up=_extrair_inteiro(dados_review.get("votes_up")),
            votes_funny=_extrair_inteiro(dados_review.get("votes_funny")),
            weighted_vote_score=_extrair_float(dados_review.get("weighted_vote_score")),
            comment_count=_extrair_inteiro(dados_review.get("comment_count")),
            steam_purchase=_extrair_bool(dados_review.get("steam_purchase")),
            received_for_free=_extrair_bool(dados_review.get("received_for_free")),
            written_during_early_access=_extrair_bool(
                dados_review.get("written_during_early_access")
            ),
            primarily_steam_deck=_extrair_bool(
                dados_review.get("primarily_steam_deck")
            ),
            developer_response=dev_resp_str,
        )
