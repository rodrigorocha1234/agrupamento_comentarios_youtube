"""Testes automatizados para o repositório de staging e Unit of Work em PostgreSQL."""

from datetime import UTC, datetime

import psycopg
import pytest

from app.dominio_contratos.modelos_dados import (
    AutorSteam,
    EventoPublicacao,
    MetadadosExecucao,
    ReviewSteam,
)
from app.persistencia_staging.conexao_postgres import ConexaoPostgresStaging
from app.persistencia_staging.esquema_postgres import EsquemaTabelasPostgres
from app.persistencia_staging.fabrica_staging import FabricaStaging
from app.persistencia_staging.repositorio_postgres import RepositorioStagingPostgres
from app.persistencia_staging.unidade_postgres import UnidadeTrabalhoPostgres


def _verificar_servidor_postgres() -> bool:
    """Verifica se o servidor PostgreSQL está online para execução dos testes."""
    try:
        gerenciador = ConexaoPostgresStaging()
        conn = gerenciador.criar_conexao()
        conn.close()
        return True
    except (psycopg.Error, OSError):
        return False


postgres_disponivel = _verificar_servidor_postgres()


@pytest.mark.skipif(
    not postgres_disponivel, reason="PostgreSQL não está acessível no momento."
)
def teste_esquema_e_transacao_postgres() -> None:
    """Verifica a criação do esquema e o comportamento atômico de commit e rollback."""
    gerenciador = ConexaoPostgresStaging()
    conn = gerenciador.criar_conexao()
    esquema = EsquemaTabelasPostgres()
    esquema.inicializar_esquema(conn)
    conn.commit()

    uow = UnidadeTrabalhoPostgres(conn)
    repo = RepositorioStagingPostgres(conn)

    metadados = MetadadosExecucao(
        id_execucao="exec_pg_teste_1",
        appid=427520,
        estrategia="historica",
        data_inicio=datetime.now(UTC),
        data_fim=None,
        status="em_execucao",
        total_paginas=0,
        total_reviews=0,
    )

    with uow:
        repo.registrar_execucao(metadados)

    # Verifica persistência após commit
    with conn.cursor() as cur:
        cur.execute(
            "SELECT status FROM execucoes_coleta WHERE id_execucao = %s;",
            ("exec_pg_teste_1",),
        )
        linha = cur.fetchone()
        assert linha is not None
        assert linha[0] == "em_execucao"


@pytest.mark.skipif(
    not postgres_disponivel, reason="PostgreSQL não está acessível no momento."
)
def teste_upsert_reviews_e_checkpoint_postgres() -> None:
    """Verifica upsert de reviews e controle de checkpoint no PostgreSQL."""
    gerenciador = ConexaoPostgresStaging()
    conn = gerenciador.criar_conexao()
    EsquemaTabelasPostgres().inicializar_esquema(conn)
    conn.commit()

    uow = UnidadeTrabalhoPostgres(conn)
    repo = RepositorioStagingPostgres(conn)

    autor = AutorSteam(
        steamid="pg_user_01",
        num_games_owned=20,
        num_reviews=2,
        playtime_forever=1000,
        playtime_last_two_weeks=50,
        playtime_at_review=800,
        last_played=1700000000,
    )

    review = ReviewSteam(
        appid=427520,
        recommendationid="REC_PG_01",
        author=autor,
        language="brazilian",
        review_texto="Excelente jogo, análise de teste PostgreSQL",
        timestamp_created=1690000000,
        timestamp_updated=1690000000,
        voted_up=True,
        votes_up=5,
        votes_funny=0,
        weighted_vote_score=0.8,
        comment_count=1,
        steam_purchase=True,
        received_for_free=False,
        written_during_early_access=False,
        primarily_steam_deck=False,
    )

    with uow:
        total = repo.salvar_lote_reviews([review])
        assert total == 1
        repo.atualizar_checkpoint(427520, "historica", "cursor_pg_100", "ok")

    ultimo_cursor = repo.obter_ultimo_checkpoint(427520, "historica")
    assert ultimo_cursor == "cursor_pg_100"


@pytest.mark.skipif(
    not postgres_disponivel, reason="PostgreSQL não está acessível no momento."
)
def teste_ciclo_outbox_postgres() -> None:
    """Verifica enfileiramento, leitura e publicação na tabela outbox PostgreSQL."""
    gerenciador = ConexaoPostgresStaging()
    conn = gerenciador.criar_conexao()
    EsquemaTabelasPostgres().inicializar_esquema(conn)
    conn.commit()

    uow = UnidadeTrabalhoPostgres(conn)
    repo = RepositorioStagingPostgres(conn)

    id_evt = f"EVT_PG_{int(datetime.now(UTC).timestamp() * 1000)}"
    evento = EventoPublicacao(
        id_evento=id_evt,
        tipo_evento="silver_reviews",
        chave_origem="silver/steam/reviews/427520_teste.parquet",
        payload_referencia='{"lote": 1}',
        status_publicacao="pendente",
        tentativas=0,
        data_criacao=datetime.now(UTC),
    )

    with uow:
        repo.enfileirar_evento_outbox(evento)

    pendentes = repo.obter_eventos_pendentes(limite=50)
    encontrado = [e for e in pendentes if e.id_evento == id_evt]
    assert len(encontrado) == 1

    with uow:
        repo.marcar_evento_publicado(id_evt)

    pendentes_apos = repo.obter_eventos_pendentes(limite=50)
    encontrado_apos = [e for e in pendentes_apos if e.id_evento == id_evt]
    assert len(encontrado_apos) == 0



def teste_fabrica_staging_postgres_resolucao() -> None:
    """Verifica que a fábrica resolve a tecnologia postgres sem if/elif no domínio."""
    fabrica = FabricaStaging()
    uow, repo = fabrica.criar_staging("postgres")
    assert isinstance(uow, UnidadeTrabalhoPostgres)
    assert isinstance(repo, RepositorioStagingPostgres)
