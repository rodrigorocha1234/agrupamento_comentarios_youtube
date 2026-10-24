"""Implementação do repositório de staging em SQLite com suporte a lotes e upsert."""

import hashlib
import itertools
import sqlite3
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import final, override

from app.dominio_contratos.modelos_dados import (
    EventoPublicacao,
    MetadadosExecucao,
    PaginaReviews,
    ReviewSteam,
)
from app.dominio_contratos.protocolos_staging import RepositorioStaging


@final
class RepositorioStagingSqlite(RepositorioStaging):
    """Repositório transacional SQLite para as tabelas de staging e controle outbox."""

    def __init__(self, conexao: sqlite3.Connection, tamanho_lote: int = 500) -> None:
        self._conexao = conexao
        self._tamanho_lote = tamanho_lote

    @override
    def registrar_execucao(self, metadados: MetadadosExecucao) -> None:
        sql = """
        INSERT INTO execucoes_coleta (
            id_execucao, appid, estrategia, data_inicio, data_fim, status,
            total_paginas, total_reviews, mensagem_erro
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id_execucao) DO UPDATE SET
            data_fim = excluded.data_fim,
            status = excluded.status,
            total_paginas = excluded.total_paginas,
            total_reviews = excluded.total_reviews,
            mensagem_erro = excluded.mensagem_erro;
        """
        data_fim_str = metadados.data_fim.isoformat() if metadados.data_fim else None
        self._conexao.execute(
            sql,
            (
                metadados.id_execucao,
                metadados.appid,
                metadados.estrategia,
                metadados.data_inicio.isoformat(),
                data_fim_str,
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
        INSERT OR IGNORE INTO paginas_recebidas (
            id_pagina, id_execucao, appid, cursor_entrada, cursor_saida,
            hash_payload, total_reviews, data_coleta
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        self._conexao.execute(
            sql,
            (
                id_pagina,
                id_execucao,
                pagina.appid,
                pagina.cursor_entrada,
                pagina.cursor_proximo,
                pagina.hash_payload,
                pagina.total_reviews_pagina,
                pagina.momento_coleta.isoformat(),
            ),
        )

    @override
    def salvar_lote_reviews(self, reviews: Sequence[ReviewSteam]) -> int:
        if not reviews:
            return 0

        total_processado = 0
        agora = datetime.now(UTC).isoformat()

        # Inserção e atualização dos autores observados
        sql_autor = """
        INSERT INTO autores_observados (
            steamid, appid, num_games_owned, num_reviews, playtime_forever,
            playtime_last_two_weeks, playtime_at_review, last_played, data_observacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(steamid, appid) DO UPDATE SET
            num_games_owned = excluded.num_games_owned,
            num_reviews = excluded.num_reviews,
            playtime_forever = excluded.playtime_forever,
            playtime_last_two_weeks = excluded.playtime_last_two_weeks,
            playtime_at_review = excluded.playtime_at_review,
            last_played = excluded.last_played,
            data_observacao = excluded.data_observacao;
        """

        # Upsert nas reviews atuais
        sql_review_atual = """
        INSERT INTO reviews_atuais (
            appid, recommendationid, steamid, language, review_texto,
            timestamp_created, timestamp_updated, voted_up, votes_up,
            votes_funny, weighted_vote_score, comment_count, steam_purchase,
            received_for_free, written_during_early_access, primarily_steam_deck,
            developer_response, hash_semantico, data_ultima_coleta
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(appid, recommendationid) DO UPDATE SET
            timestamp_updated = excluded.timestamp_updated,
            voted_up = excluded.voted_up,
            votes_up = excluded.votes_up,
            votes_funny = excluded.votes_funny,
            weighted_vote_score = excluded.weighted_vote_score,
            comment_count = excluded.comment_count,
            developer_response = excluded.developer_response,
            hash_semantico = excluded.hash_semantico,
            data_ultima_coleta = excluded.data_ultima_coleta;
        """

        # Inserção no histórico
        sql_historico = """
        INSERT OR IGNORE INTO reviews_historico (
            appid, recommendationid, versao_registro, steamid, timestamp_updated,
            voted_up, votes_up, weighted_vote_score, comment_count,
            hash_semantico, data_captura
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        # Processar lotes tipados com itertools.batched
        for lote in itertools.batched(reviews, self._tamanho_lote):
            dados_autores: list[tuple[object, ...]] = []
            dados_reviews: list[tuple[object, ...]] = []
            dados_historico: list[tuple[object, ...]] = []

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
                        1 if rev.voted_up else 0,
                        rev.votes_up,
                        rev.votes_funny,
                        rev.weighted_vote_score,
                        rev.comment_count,
                        1 if rev.steam_purchase else 0,
                        1 if rev.received_for_free else 0,
                        1 if rev.written_during_early_access else 0,
                        1 if rev.primarily_steam_deck else 0,
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
                        1 if rev.voted_up else 0,
                        rev.votes_up,
                        rev.weighted_vote_score,
                        rev.comment_count,
                        hash_semantico,
                        agora,
                    )
                )

            self._conexao.executemany(sql_autor, dados_autores)
            self._conexao.executemany(sql_review_atual, dados_reviews)
            self._conexao.executemany(sql_historico, dados_historico)
            total_processado += len(lote)

        return total_processado

    @override
    def atualizar_checkpoint(
        self, appid: int, estrategia: str, cursor: str, status: str
    ) -> None:
        sql = """
        INSERT INTO marcadores_coleta (appid, estrategia, cursor_atual, data_atualizacao, status)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(appid, estrategia) DO UPDATE SET
            cursor_atual = excluded.cursor_atual,
            data_atualizacao = excluded.data_atualizacao,
            status = excluded.status;
        """
        agora = datetime.now(UTC).isoformat()
        self._conexao.execute(sql, (appid, estrategia, cursor, agora, status))

    @override
    def obter_ultimo_checkpoint(self, appid: int, estrategia: str) -> str | None:
        sql = "SELECT cursor_atual FROM marcadores_coleta WHERE appid = ? AND estrategia = ?;"
        cursor = self._conexao.execute(sql, (appid, estrategia))
        linha = cursor.fetchone()
        if linha and linha[0]:
            return str(linha[0])
        return None

    @override
    def enfileirar_evento_outbox(self, evento: EventoPublicacao) -> None:
        sql = """
        INSERT INTO eventos_publicacao (
            id_evento, tipo_evento, chave_origem, payload_referencia,
            status_publicacao, tentativas, data_criacao, data_publicacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        data_pub = (
            evento.data_publicacao.isoformat() if evento.data_publicacao else None
        )
        self._conexao.execute(
            sql,
            (
                evento.id_evento,
                evento.tipo_evento,
                evento.chave_origem,
                evento.payload_referencia,
                evento.status_publicacao,
                evento.tentativas,
                evento.data_criacao.isoformat(),
                data_pub,
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
        LIMIT ?;
        """
        cursor = self._conexao.execute(sql, (limite,))
        linhas = cursor.fetchall()

        eventos: list[EventoPublicacao] = []
        for l in linhas:
            dt_criacao = datetime.fromisoformat(l["data_criacao"])
            dt_pub = (
                datetime.fromisoformat(l["data_publicacao"])
                if l["data_publicacao"]
                else None
            )
            eventos.append(
                EventoPublicacao(
                    id_evento=str(l["id_evento"]),
                    tipo_evento=str(l["tipo_evento"]),
                    chave_origem=str(l["chave_origem"]),
                    payload_referencia=str(l["payload_referencia"]),
                    status_publicacao=str(l["status_publicacao"]),
                    tentativas=int(l["tentativas"]),
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
            data_publicacao = ?
        WHERE id_evento = ?;
        """
        agora = datetime.now(UTC).isoformat()
        self._conexao.execute(sql, (agora, id_evento))
