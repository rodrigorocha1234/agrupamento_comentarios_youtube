"""Implementação do repositório de staging em PostgreSQL com lotes e upsert idempotente."""

import hashlib
import itertools
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import final, override

import psycopg

from app.dominio_contratos.modelos_dados import (
    EventoPublicacao,
    MetadadosExecucao,
    PaginaReviews,
    ReviewSteam,
    TipoParametroSql,
)
from app.dominio_contratos.protocolos_staging import RepositorioStaging


@final
class RepositorioStagingPostgres(RepositorioStaging):
    """Repositório transacional PostgreSQL para staging e controle de eventos outbox."""

    def __init__(
        self, conexao: psycopg.Connection[tuple[TipoParametroSql, ...]], tamanho_lote: int = 500
    ) -> None:
        self._conexao = conexao
        self._tamanho_lote = tamanho_lote


    @override
    def registrar_execucao(self, metadados: MetadadosExecucao) -> None:
        sql = """
        INSERT INTO execucoes_coleta (
            id_execucao, appid, estrategia, data_inicio, data_fim, status,
            total_paginas, total_reviews, mensagem_erro
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(id_execucao) DO UPDATE SET
            data_fim = EXCLUDED.data_fim,
            status = EXCLUDED.status,
            total_paginas = EXCLUDED.total_paginas,
            total_reviews = EXCLUDED.total_reviews,
            mensagem_erro = EXCLUDED.mensagem_erro;
        """
        with self._conexao.cursor() as cur:
            cur.execute(
                sql,
                (
                    metadados.id_execucao,
                    metadados.appid,
                    metadados.estrategia,
                    metadados.data_inicio,
                    metadados.data_fim,
                    metadados.status,
                    metadados.total_paginas,
                    metadados.total_reviews,
                    metadados.mensagem_erro,
                ),
            )

    @override
    def gravar_pagina(self, pagina: PaginaReviews, id_execucao: str) -> None:
        id_pagina = f"{pagina.appid}_{pagina.hash_payload[:16]}_{pagina.cursor_entrada}"
        sql = """
        INSERT INTO paginas_recebidas (
            id_pagina, id_execucao, appid, cursor_entrada, cursor_saida,
            hash_payload, total_reviews, data_coleta
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id_pagina) DO NOTHING;
        """
        with self._conexao.cursor() as cur:
            cur.execute(
                sql,
                (
                    id_pagina,
                    id_execucao,
                    pagina.appid,
                    pagina.cursor_entrada,
                    pagina.cursor_proximo,
                    pagina.hash_payload,
                    pagina.total_reviews_pagina,
                    pagina.momento_coleta,
                ),
            )

    @override
    def salvar_lote_reviews(self, reviews: Sequence[ReviewSteam]) -> int:
        if not reviews:
            return 0

        total_processado = 0
        agora = datetime.now(UTC)

        sql_autor = """
        INSERT INTO autores_observados (
            steamid, appid, num_games_owned, num_reviews, playtime_forever,
            playtime_last_two_weeks, playtime_at_review, last_played, data_observacao
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(steamid, appid) DO UPDATE SET
            num_games_owned = EXCLUDED.num_games_owned,
            num_reviews = EXCLUDED.num_reviews,
            playtime_forever = EXCLUDED.playtime_forever,
            playtime_last_two_weeks = EXCLUDED.playtime_last_two_weeks,
            playtime_at_review = EXCLUDED.playtime_at_review,
            last_played = EXCLUDED.last_played,
            data_observacao = EXCLUDED.data_observacao;
        """

        sql_review_atual = """
        INSERT INTO reviews_atuais (
            appid, recommendationid, steamid, language, review_texto,
            timestamp_created, timestamp_updated, voted_up, votes_up,
            votes_funny, weighted_vote_score, comment_count, steam_purchase,
            received_for_free, written_during_early_access, primarily_steam_deck,
            developer_response, hash_semantico, data_ultima_coleta
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(appid, recommendationid) DO UPDATE SET
            timestamp_updated = EXCLUDED.timestamp_updated,
            voted_up = EXCLUDED.voted_up,
            votes_up = EXCLUDED.votes_up,
            votes_funny = EXCLUDED.votes_funny,
            weighted_vote_score = EXCLUDED.weighted_vote_score,
            comment_count = EXCLUDED.comment_count,
            developer_response = EXCLUDED.developer_response,
            hash_semantico = EXCLUDED.hash_semantico,
            data_ultima_coleta = EXCLUDED.data_ultima_coleta;
        """

        sql_historico = """
        INSERT INTO reviews_historico (
            appid, recommendationid, versao_registro, steamid, timestamp_updated,
            voted_up, votes_up, weighted_vote_score, comment_count,
            hash_semantico, data_captura
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(appid, recommendationid, versao_registro) DO NOTHING;
        """

        for lote in itertools.batched(reviews, self._tamanho_lote):
            dados_autores: list[tuple[TipoParametroSql, ...]] = []
            dados_reviews: list[tuple[TipoParametroSql, ...]] = []
            dados_historico: list[tuple[TipoParametroSql, ...]] = []

            for rev in lote:
                aut = rev.author
                dados_autores.append(
                    (
                        aut.steamid,
                        rev.appid,
                        aut.num_games_owned,
                        aut.num_reviews,
                        aut.playtime_forever,
                        aut.playtime_last_two_weeks,
                        aut.playtime_at_review,
                        aut.last_played,
                        agora,
                    )
                )

                conteudo_hash = f"{rev.timestamp_updated}_{rev.voted_up}_{rev.votes_up}_{rev.weighted_vote_score}"
                hash_semantico = hashlib.md5(conteudo_hash.encode("utf-8")).hexdigest()

                dados_reviews.append(
                    (
                        rev.appid,
                        rev.recommendationid,
                        aut.steamid,
                        rev.language,
                        rev.review_texto,
                        rev.timestamp_created,
                        rev.timestamp_updated,
                        rev.voted_up,
                        rev.votes_up,
                        rev.votes_funny,
                        rev.weighted_vote_score,
                        rev.comment_count,
                        rev.steam_purchase,
                        rev.received_for_free,
                        rev.written_during_early_access,
                        rev.primarily_steam_deck,
                        rev.developer_response,
                        hash_semantico,
                        agora,
                    )
                )

                versao = int(rev.timestamp_updated)
                dados_historico.append(
                    (
                        rev.appid,
                        rev.recommendationid,
                        versao,
                        aut.steamid,
                        rev.timestamp_updated,
                        rev.voted_up,
                        rev.votes_up,
                        rev.weighted_vote_score,
                        rev.comment_count,
                        hash_semantico,
                        agora,
                    )
                )

            with self._conexao.cursor() as cur:
                cur.executemany(sql_autor, dados_autores)
                cur.executemany(sql_review_atual, dados_reviews)
                cur.executemany(sql_historico, dados_historico)
            total_processado += len(lote)

        return total_processado

    @override
    def atualizar_checkpoint(
        self, appid: int, estrategia: str, cursor: str, status: str
    ) -> None:
        sql = """
        INSERT INTO marcadores_coleta (appid, estrategia, cursor_atual, data_atualizacao, status)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT(appid, estrategia) DO UPDATE SET
            cursor_atual = EXCLUDED.cursor_atual,
            data_atualizacao = EXCLUDED.data_atualizacao,
            status = EXCLUDED.status;
        """
        agora = datetime.now(UTC)
        with self._conexao.cursor() as cur:
            cur.execute(sql, (appid, estrategia, cursor, agora, status))

    @override
    def obter_ultimo_checkpoint(self, appid: int, estrategia: str) -> str | None:
        sql = "SELECT cursor_atual FROM marcadores_coleta WHERE appid = %s AND estrategia = %s;"
        with self._conexao.cursor() as cur:
            cur.execute(sql, (appid, estrategia))
            linha = cur.fetchone()
            if linha and linha[0]:
                return str(linha[0])
        return None

    @override
    def enfileirar_evento_outbox(self, evento: EventoPublicacao) -> None:
        sql = """
        INSERT INTO eventos_publicacao (
            id_evento, tipo_evento, chave_origem, payload_referencia,
            status_publicacao, tentativas, data_criacao, data_publicacao
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(id_evento) DO NOTHING;
        """
        with self._conexao.cursor() as cur:
            cur.execute(
                sql,
                (
                    evento.id_evento,
                    evento.tipo_evento,
                    evento.chave_origem,
                    evento.payload_referencia,
                    evento.status_publicacao,
                    evento.tentativas,
                    evento.data_criacao,
                    evento.data_publicacao,
                ),
            )

    @override
    def obter_eventos_pendentes(self, limite: int = 100) -> Sequence[EventoPublicacao]:
        sql = """
        SELECT id_evento, tipo_evento, chave_origem, payload_referencia,
               status_publicacao, tentativas, data_criacao, data_publicacao
        FROM eventos_publicacao
        WHERE status_publicacao = 'pendente'
        ORDER BY data_criacao ASC
        LIMIT %s;
        """
        eventos: list[EventoPublicacao] = []
        with self._conexao.cursor() as cur:
            cur.execute(sql, (limite,))
            linhas = cur.fetchall()
            for l in linhas:
                dt_criacao = (
                    l[6]
                    if isinstance(l[6], datetime)
                    else datetime.fromisoformat(str(l[6]))
                )
                dt_pub = (
                    l[7]
                    if isinstance(l[7], datetime)
                    else (datetime.fromisoformat(str(l[7])) if l[7] else None)
                )
                eventos.append(
                    EventoPublicacao(
                        id_evento=str(l[0]),
                        tipo_evento=str(l[1]),
                        chave_origem=str(l[2]),
                        payload_referencia=str(l[3]),
                        status_publicacao=str(l[4]),
                        tentativas=int(str(l[5])),
                        data_criacao=dt_criacao,

                        data_publicacao=dt_pub,
                    )
                )
        return tuple(eventos)

    @override
    def marcar_evento_publicado(self, id_evento: str) -> None:
        sql = """
        UPDATE eventos_publicacao
        SET status_publicacao = 'publicado',
            data_publicacao = %s
        WHERE id_evento = %s;
        """
        agora = datetime.now(UTC)
        with self._conexao.cursor() as cur:
            cur.execute(sql, (agora, id_evento))
