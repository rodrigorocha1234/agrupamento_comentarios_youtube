"""Definição do esquema de tabelas relacionais de staging para PostgreSQL."""

from typing import final

import psycopg

from app.dominio_contratos.modelos_dados import TipoParametroSql


@final
class EsquemaTabelasPostgres:
    """Responsável pela criação idempotente do esquema de staging no PostgreSQL."""

    def inicializar_esquema(self, conexao: psycopg.Connection[tuple[TipoParametroSql, ...]]) -> None:
        """Executa comandos DDL para criação das tabelas e índices de staging."""

        sql_ddl = """
        CREATE TABLE IF NOT EXISTS execucoes_coleta (
            id_execucao VARCHAR(64) PRIMARY KEY,
            appid BIGINT NOT NULL,
            estrategia VARCHAR(32) NOT NULL,
            data_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
            data_fim TIMESTAMP WITH TIME ZONE,
            status VARCHAR(16) NOT NULL,
            total_paginas INTEGER NOT NULL,
            total_reviews INTEGER NOT NULL,
            mensagem_erro TEXT
        );

        CREATE TABLE IF NOT EXISTS paginas_recebidas (
            id_pagina VARCHAR(128) PRIMARY KEY,
            id_execucao VARCHAR(64) NOT NULL,
            appid BIGINT NOT NULL,
            cursor_entrada TEXT NOT NULL,
            cursor_saida TEXT,
            hash_payload VARCHAR(64) NOT NULL,
            total_reviews INTEGER NOT NULL,
            data_coleta TIMESTAMP WITH TIME ZONE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS autores_observados (
            steamid VARCHAR(32) NOT NULL,
            appid BIGINT NOT NULL,
            num_games_owned INTEGER NOT NULL,
            num_reviews INTEGER NOT NULL,
            playtime_forever BIGINT NOT NULL,
            playtime_last_two_weeks BIGINT NOT NULL,
            playtime_at_review BIGINT NOT NULL,
            last_played BIGINT NOT NULL,
            data_observacao TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (steamid, appid)
        );

        CREATE TABLE IF NOT EXISTS reviews_atuais (
            appid BIGINT NOT NULL,
            recommendationid VARCHAR(32) NOT NULL,
            steamid VARCHAR(32) NOT NULL,
            language VARCHAR(32) NOT NULL,
            review_texto TEXT NOT NULL,
            timestamp_created BIGINT NOT NULL,
            timestamp_updated BIGINT NOT NULL,
            voted_up BOOLEAN NOT NULL,
            votes_up INTEGER NOT NULL,
            votes_funny INTEGER NOT NULL,
            weighted_vote_score DOUBLE PRECISION NOT NULL,
            comment_count INTEGER NOT NULL,
            steam_purchase BOOLEAN NOT NULL,
            received_for_free BOOLEAN NOT NULL,
            written_during_early_access BOOLEAN NOT NULL,
            primarily_steam_deck BOOLEAN NOT NULL,
            developer_response TEXT,
            hash_semantico VARCHAR(32) NOT NULL,
            data_ultima_coleta TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (appid, recommendationid)
        );

        CREATE TABLE IF NOT EXISTS reviews_historico (
            appid BIGINT NOT NULL,
            recommendationid VARCHAR(32) NOT NULL,
            versao_registro BIGINT NOT NULL,
            steamid VARCHAR(32) NOT NULL,
            timestamp_updated BIGINT NOT NULL,
            voted_up BOOLEAN NOT NULL,
            votes_up INTEGER NOT NULL,
            weighted_vote_score DOUBLE PRECISION NOT NULL,
            comment_count INTEGER NOT NULL,
            hash_semantico VARCHAR(32) NOT NULL,
            data_captura TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (appid, recommendationid, versao_registro)
        );

        CREATE TABLE IF NOT EXISTS marcadores_coleta (
            appid BIGINT NOT NULL,
            estrategia VARCHAR(32) NOT NULL,
            cursor_atual TEXT NOT NULL,
            data_atualizacao TIMESTAMP WITH TIME ZONE NOT NULL,
            status VARCHAR(16) NOT NULL,
            PRIMARY KEY (appid, estrategia)
        );

        CREATE TABLE IF NOT EXISTS eventos_publicacao (
            id_evento VARCHAR(64) PRIMARY KEY,
            tipo_evento VARCHAR(32) NOT NULL,
            chave_origem VARCHAR(256) NOT NULL,
            payload_referencia TEXT NOT NULL,
            status_publicacao VARCHAR(16) NOT NULL,
            tentativas INTEGER NOT NULL,
            data_criacao TIMESTAMP WITH TIME ZONE NOT NULL,
            data_publicacao TIMESTAMP WITH TIME ZONE
        );

        CREATE INDEX IF NOT EXISTS idx_pg_reviews_atual_appid ON reviews_atuais(appid);
        CREATE INDEX IF NOT EXISTS idx_pg_outbox_pendente ON eventos_publicacao(status_publicacao, data_criacao);
        """
        with conexao.cursor() as cur:
            cur.execute(sql_ddl)
