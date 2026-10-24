"""Testes automatizados para persistência de staging SQLite e controle transacional."""

import sqlite3
from datetime import UTC, datetime

import pytest

from app.dominio_contratos.modelos_dados import (
    AutorSteam,
    EventoPublicacao,
    ReviewSteam,
)
from app.persistencia_staging.esquema_tabelas import EsquemaTabelasStaging
from app.persistencia_staging.repositorio_sqlite import RepositorioStagingSqlite
from app.persistencia_staging.unidade_trabalho import UnidadeTrabalhoSqlite


@pytest.fixture
def conexao_memoria() -> sqlite3.Connection:
    """Fornece uma conexão SQLite em memória com esquema inicializado."""
    conexao = sqlite3.connect(":memory:", autocommit=False)
    conexao.row_factory = sqlite3.Row
    esquema = EsquemaTabelasStaging()
    esquema.inicializar_esquema(conexao)
    return conexao


def teste_inicializacao_esquema(conexao_memoria: sqlite3.Connection) -> None:
    """Verifica se todas as 7 tabelas estruturais foram criadas."""
    cursor = conexao_memoria.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    )
    tabelas = [row["name"] for row in cursor.fetchall()]

    tabelas_esperadas = [
        "autores_observados",
        "eventos_publicacao",
        "execucoes_coleta",
        "marcadores_coleta",
        "paginas_recebidas",
        "reviews_atuais",
        "reviews_historico",
    ]
    for tabela in tabelas_esperadas:
        assert tabela in tabelas


def teste_transacao_commit_e_rollback(conexao_memoria: sqlite3.Connection) -> None:
    """Verifica que a UnidadeTrabalho desfaz operações quando ocorre erro."""
    uow = UnidadeTrabalhoSqlite(conexao_memoria)
    repo = RepositorioStagingSqlite(conexao_memoria)

    # Inserção bem-sucedida com commit explícito
    with uow:
        repo.atualizar_checkpoint(427520, "recente", "cursor_valido", "ativo")

    assert repo.obter_ultimo_checkpoint(427520, "recente") == "cursor_valido"

    # Tentativa com falha simulada dentro do bloco
    try:
        with uow:
            repo.atualizar_checkpoint(427520, "recente", "cursor_falho", "erro")
            raise RuntimeError("Falha proposital para rollback")
    except RuntimeError:
        pass

    # Deve manter o cursor anterior após o rollback
    assert repo.obter_ultimo_checkpoint(427520, "recente") == "cursor_valido"


def teste_upsert_reviews_e_historico(conexao_memoria: sqlite3.Connection) -> None:
    """Verifica que avaliações atualizadas não duplicam na tabela atual e geram histórico."""
    uow = UnidadeTrabalhoSqlite(conexao_memoria)
    repo = RepositorioStagingSqlite(conexao_memoria)

    autor = AutorSteam(
        steamid="12345",
        num_games_owned=10,
        num_reviews=2,
        playtime_forever=1000,
        playtime_last_two_weeks=50,
        playtime_at_review=500,
        last_played=1700000000,
    )

    review_v1 = ReviewSteam(
        appid=427520,
        recommendationid="REC_99",
        author=autor,
        language="brazilian",
        review_texto="Versão inicial",
        timestamp_created=1690000000,
        timestamp_updated=1690000000,
        voted_up=True,
        votes_up=5,
        votes_funny=0,
        weighted_vote_score=0.7,
        comment_count=0,
        steam_purchase=True,
        received_for_free=False,
        written_during_early_access=False,
        primarily_steam_deck=False,
    )

    with uow:
        repo.salvar_lote_reviews([review_v1])

    # Verificar inserção
    cursor = conexao_memoria.execute("SELECT COUNT(*) FROM reviews_atuais;")
    assert cursor.fetchone()[0] == 1

    # Atualização da mesma review (mesmo recommendationid, novo timestamp e votos)
    review_v2 = ReviewSteam(
        appid=427520,
        recommendationid="REC_99",
        author=autor,
        language="brazilian",
        review_texto="Versão editada",
        timestamp_created=1690000000,
        timestamp_updated=1690500000,
        voted_up=True,
        votes_up=15,
        votes_funny=2,
        weighted_vote_score=0.9,
        comment_count=3,
        steam_purchase=True,
        received_for_free=False,
        written_during_early_access=False,
        primarily_steam_deck=False,
    )

    with uow:
        repo.salvar_lote_reviews([review_v2])

    # Tabela atual continua com apenas 1 registro atualizado
    cursor = conexao_memoria.execute(
        "SELECT votes_up, comment_count FROM reviews_atuais WHERE recommendationid='REC_99';"
    )
    linha = cursor.fetchone()
    assert linha["votes_up"] == 15
    assert linha["comment_count"] == 3

    # Tabela de histórico deve conter as 2 versões
    cursor_hist = conexao_memoria.execute(
        "SELECT COUNT(*) FROM reviews_historico WHERE recommendationid='REC_99';"
    )
    assert cursor_hist.fetchone()[0] == 2


def teste_ciclo_outbox(conexao_memoria: sqlite3.Connection) -> None:
    """Valida enfileiramento, leitura de pendentes e confirmação de eventos outbox."""
    uow = UnidadeTrabalhoSqlite(conexao_memoria)
    repo = RepositorioStagingSqlite(conexao_memoria)

    evento = EventoPublicacao(
        id_evento="EVT_001",
        tipo_evento="bronze_pagina",
        chave_origem="bronze/steam/pagina_1.json",
        payload_referencia='{"teste": true}',
        status_publicacao="pendente",
        tentativas=0,
        data_criacao=datetime.now(UTC),
    )

    with uow:
        repo.enfileirar_evento_outbox(evento)

    pendentes = repo.obter_eventos_pendentes(limite=10)
    assert len(pendentes) == 1
    assert pendentes[0].id_evento == "EVT_001"

    with uow:
        repo.marcar_evento_publicado("EVT_001")

    # Não deve mais constar como pendente
    pendentes_apos = repo.obter_eventos_pendentes(limite=10)
    assert len(pendentes_apos) == 0
