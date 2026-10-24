"""Definição DDL e inicialização idempotente das tabelas relacionais do staging."""

import sqlite3
from typing import final


@final
class EsquemaTabelasStaging:
    """Cria e valida as 7 tabelas estruturais de staging transacional."""

    _DDL_EXECUCOES: str = """
    CREATE TABLE IF NOT EXISTS execucoes_coleta (
        id_execucao TEXT PRIMARY KEY,
        appid INTEGER NOT NULL,
        estrategia TEXT NOT NULL,
        data_inicio TEXT NOT NULL,
        data_fim TEXT,
        status TEXT NOT NULL,
        total_paginas INTEGER DEFAULT 0,
        total_reviews INTEGER DEFAULT 0,
        mensagem_erro TEXT
    );
    """

    _DDL_PAGINAS: str = """
    CREATE TABLE IF NOT EXISTS paginas_recebidas (
        id_pagina TEXT PRIMARY KEY,
        id_execucao TEXT NOT NULL,
        appid INTEGER NOT NULL,
        cursor_entrada TEXT NOT NULL,
        cursor_saida TEXT,
        hash_payload TEXT NOT NULL,
        total_reviews INTEGER NOT NULL,
        data_coleta TEXT NOT NULL,
        FOREIGN KEY (id_execucao) REFERENCES execucoes_coleta (id_execucao)
    );
    """

    _DDL_REVIEWS_ATUAIS: str = """
    CREATE TABLE IF NOT EXISTS reviews_atuais (
        appid INTEGER NOT NULL,
        recommendationid TEXT NOT NULL,
        steamid TEXT NOT NULL,
        language TEXT NOT NULL,
        review_texto TEXT NOT NULL,
        timestamp_created INTEGER NOT NULL,
        timestamp_updated INTEGER NOT NULL,
        voted_up INTEGER NOT NULL,
        votes_up INTEGER NOT NULL,
        votes_funny INTEGER NOT NULL,
        weighted_vote_score REAL NOT NULL,
        comment_count INTEGER NOT NULL,
        steam_purchase INTEGER NOT NULL,
        received_for_free INTEGER NOT NULL,
        written_during_early_access INTEGER NOT NULL,
        primarily_steam_deck INTEGER NOT NULL,
        developer_response TEXT,
        hash_semantico TEXT NOT NULL,
        data_ultima_coleta TEXT NOT NULL,
        PRIMARY KEY (appid, recommendationid)
    );
    """

    _DDL_REVIEWS_HISTORICO: str = """
    CREATE TABLE IF NOT EXISTS reviews_historico (
        appid INTEGER NOT NULL,
        recommendationid TEXT NOT NULL,
        versao_registro INTEGER NOT NULL,
        steamid TEXT NOT NULL,
        timestamp_updated INTEGER NOT NULL,
        voted_up INTEGER NOT NULL,
        votes_up INTEGER NOT NULL,
        weighted_vote_score REAL NOT NULL,
        comment_count INTEGER NOT NULL,
        hash_semantico TEXT NOT NULL,
        data_captura TEXT NOT NULL,
        PRIMARY KEY (appid, recommendationid, versao_registro)
    );
    """

    _DDL_AUTORES: str = """
    CREATE TABLE IF NOT EXISTS autores_observados (
        steamid TEXT NOT NULL,
        appid INTEGER NOT NULL,
        num_games_owned INTEGER NOT NULL,
        num_reviews INTEGER NOT NULL,
        playtime_forever INTEGER NOT NULL,
        playtime_last_two_weeks INTEGER NOT NULL,
        playtime_at_review INTEGER NOT NULL,
        last_played INTEGER NOT NULL,
        data_observacao TEXT NOT NULL,
        PRIMARY KEY (steamid, appid)
    );
    """

    _DDL_MARCADORES: str = """
    CREATE TABLE IF NOT EXISTS marcadores_coleta (
        appid INTEGER NOT NULL,
        estrategia TEXT NOT NULL,
        cursor_atual TEXT NOT NULL,
        data_atualizacao TEXT NOT NULL,
        status TEXT NOT NULL,
        PRIMARY KEY (appid, estrategia)
    );
    """

    _DDL_OUTBOX: str = """
    CREATE TABLE IF NOT EXISTS eventos_publicacao (
        id_evento TEXT PRIMARY KEY,
        tipo_evento TEXT NOT NULL,
        chave_origem TEXT NOT NULL,
        payload_referencia TEXT NOT NULL,
        status_publicacao TEXT NOT NULL,
        tentativas INTEGER DEFAULT 0,
        data_criacao TEXT NOT NULL,
        data_publicacao TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_outbox_status ON eventos_publicacao (status_publicacao);
    """

    def inicializar_esquema(self, conexao: sqlite3.Connection) -> None:
        """Cria todas as tabelas e índices se ainda não existirem."""
        with conexao:
            conexao.execute(self._DDL_EXECUCOES)
            conexao.execute(self._DDL_PAGINAS)
            conexao.execute(self._DDL_REVIEWS_ATUAIS)
            conexao.execute(self._DDL_REVIEWS_HISTORICO)
            conexao.execute(self._DDL_AUTORES)
            conexao.execute(self._DDL_MARCADORES)
            conexao.executescript(self._DDL_OUTBOX)
