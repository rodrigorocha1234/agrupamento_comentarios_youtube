"""Teste de integração ponta a ponta do pipeline de extração, staging e outbox."""

import sqlite3

from app.configuracao_geral.conf_yaml import ConfYAML
from app.extracao_steam.gerador_paginas import GeradorPaginasSteam
from app.gestao_datalake.despachante_outbox import DespachanteOutbox
from app.gestao_datalake.escritor_prata import EscritorCamadaPrata
from app.observabilidade_metricas.registro_telemetria import RegistroTelemetria
from app.observabilidade_metricas.validador_qualidade import ValidadorQualidadeDados
from app.orquestracao_pipeline.executor_coleta import ExecutorColetaStaging
from app.persistencia_staging.esquema_tabelas import EsquemaTabelasStaging
from app.persistencia_staging.repositorio_sqlite import RepositorioStagingSqlite
from app.persistencia_staging.unidade_trabalho import UnidadeTrabalhoSqlite
from tests.teste_datalake import ArmazenamentoLakeFalso
from tests.teste_extracao import ClienteSteamFalso


def teste_ciclo_completo_integrado() -> None:
    """Executa o ciclo completo da Fase 1 e valida a persistência em todas as camadas."""
    conf = ConfYAML()

    # Banco staging em memória
    conexao = sqlite3.connect(":memory:", autocommit=False)
    conexao.row_factory = sqlite3.Row
    EsquemaTabelasStaging().inicializar_esquema(conexao)

    uow = UnidadeTrabalhoSqlite(conexao)
    repo = RepositorioStagingSqlite(conexao)

    # Lakehouse mock em memória
    lake = ArmazenamentoLakeFalso()
    despachante = DespachanteOutbox(repo, lake)
    escritor_prata = EscritorCamadaPrata(lake)

    # Cliente com 2 páginas mockadas
    cliente_falso = ClienteSteamFalso()
    gerador = GeradorPaginasSteam(cliente=cliente_falso, maximo_paginas=5)

    telemetria = RegistroTelemetria()
    validador = ValidadorQualidadeDados()

    executor = ExecutorColetaStaging(
        configuracoes=conf,
        gerador_paginas=gerador,
        uow=uow,
        repositorio=repo,
        despachante_outbox=despachante,
        escritor_prata=escritor_prata,
        validador=validador,
        telemetria=telemetria,
    )

    resultado = executor.executar_coleta_jogo(appid=427520, estrategia="recente")

    # Asserções no resultado da execução
    assert resultado.status == "concluido"
    assert resultado.total_paginas == 2
    assert resultado.total_reviews == 2
    assert resultado.mensagem_erro is None

    # Asserções no banco de staging
    cursor_rev = conexao.execute(
        "SELECT COUNT(*) FROM reviews_atuais WHERE appid = 427520;"
    )
    assert cursor_rev.fetchone()[0] == 2

    cursor_aut = conexao.execute(
        "SELECT COUNT(*) FROM autores_observados WHERE appid = 427520;"
    )
    assert cursor_aut.fetchone()[0] == 2

    cursor_exec = conexao.execute(
        "SELECT status FROM execucoes_coleta WHERE id_execucao = ?;",
        (resultado.id_execucao,),
    )
    assert cursor_exec.fetchone()["status"] == "concluido"

    # Asserções na outbox e Lakehouse
    cursor_outbox = conexao.execute(
        "SELECT COUNT(*) FROM eventos_publicacao WHERE status_publicacao = 'publicado';"
    )
    assert cursor_outbox.fetchone()[0] == 2

    # Camada Silver (Parquet) gravada no lake
    assert len(lake.arquivos_binarios) == 2
