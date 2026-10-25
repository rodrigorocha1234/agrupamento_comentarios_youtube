"""Testes automatizados para persistência em camadas Bronze e Silver do Data Lake."""

import sqlite3
from datetime import UTC, datetime
from typing import final, override

from app.dominio_contratos.modelos_dados import (
    AutorSteam,
    EventoPublicacao,
    ReviewSteam,
)
from app.dominio_contratos.protocolos_datalake import ArmazenamentoLake
from app.gestao_datalake.despachante_outbox import DespachanteOutbox
from app.gestao_datalake.escritor_bronze import EscritorCamadaBronze
from app.gestao_datalake.escritor_prata import EscritorCamadaPrata
from app.persistencia_staging.esquema_tabelas import EsquemaTabelasStaging
from app.persistencia_staging.repositorio_sqlite import RepositorioStagingSqlite
from app.persistencia_staging.unidade_trabalho import UnidadeTrabalhoSqlite


@final
class ArmazenamentoLakeFalso(ArmazenamentoLake):
    """Implementação em memória de ArmazenamentoLake para testes."""

    def __init__(self) -> None:
        self.textos: dict[str, str] = {}
        self.arquivos_binarios: dict[str, bytes] = {}

    @property
    @override
    def bucket(self) -> str:
        return "steam-reviews-teste"

    @override
    def gravar_texto(self, caminho_chave: str, conteudo: str) -> None:
        self.textos[caminho_chave] = conteudo

    @override
    def gravar_bytes(self, caminho_chave: str, dados_bytes: bytes) -> None:
        self.arquivos_binarios[caminho_chave] = dados_bytes

    @override
    def ler_bytes(self, caminho_chave: str) -> bytes:
        if caminho_chave in self.arquivos_binarios:
            return self.arquivos_binarios[caminho_chave]
        if caminho_chave in self.textos:
            return self.textos[caminho_chave].encode("utf-8")
        raise FileNotFoundError(f"Chave '{caminho_chave}' não encontrada.")

    @override
    def listar_chaves(self, prefixo: str) -> list[str]:
        prefixo_limpo = prefixo.lstrip("/")
        todas = list(self.arquivos_binarios.keys()) + list(self.textos.keys())
        return [k for k in todas if k.lstrip("/").startswith(prefixo_limpo)]

    @override
    def verificar_existencia(self, caminho_chave: str) -> bool:
        return caminho_chave in self.textos or caminho_chave in self.arquivos_binarios


def teste_escritor_bronze_imutabilidade() -> None:
    """Verifica particionamento e preservação de imutabilidade na camada Bronze."""
    lake = ArmazenamentoLakeFalso()
    escritor = EscritorCamadaBronze(lake)

    caminho = escritor.salvar_pagina_bruta(
        appid=427520,
        data_coleta="2026-10-24",
        id_execucao="exec_1",
        numero_pagina=1,
        conteudo_json='{"reviews": []}',
    )

    assert caminho in lake.textos
    assert lake.textos[caminho] == '{"reviews": []}'

    # Tentativa de sobrescrita com novo conteúdo não altera conteúdo prévio
    escritor.salvar_pagina_bruta(
        appid=427520,
        data_coleta="2026-10-24",
        id_execucao="exec_1",
        numero_pagina=1,
        conteudo_json='{"novo": true}',
    )
    assert lake.textos[caminho] == '{"reviews": []}'


def teste_escritor_prata_parquet() -> None:
    """Verifica a serialização colunar Parquet para a camada Silver."""
    lake = ArmazenamentoLakeFalso()
    escritor = EscritorCamadaPrata(lake)

    autor = AutorSteam(
        steamid="999",
        num_games_owned=5,
        num_reviews=1,
        playtime_forever=200,
        playtime_last_two_weeks=10,
        playtime_at_review=150,
        last_played=1700000000,
    )
    review = ReviewSteam(
        appid=427520,
        recommendationid="REC_SILVER",
        author=autor,
        language="brazilian",
        review_texto="Texto da review",
        timestamp_created=1690000000,
        timestamp_updated=1690000000,
        voted_up=True,
        votes_up=1,
        votes_funny=0,
        weighted_vote_score=0.5,
        comment_count=0,
        steam_purchase=True,
        received_for_free=False,
        written_during_early_access=False,
        primarily_steam_deck=False,
    )

    caminho = escritor.salvar_lote_parquet(427520, "lote_01", [review])
    assert caminho in lake.arquivos_binarios
    assert len(lake.arquivos_binarios[caminho]) > 0


def teste_despachante_outbox_integracao() -> None:
    """Garante que o DespachanteOutbox publica eventos pendentes e atualiza o staging."""
    lake = ArmazenamentoLakeFalso()
    conexao = sqlite3.connect(":memory:", autocommit=False)
    conexao.row_factory = sqlite3.Row
    EsquemaTabelasStaging().inicializar_esquema(conexao)

    uow = UnidadeTrabalhoSqlite(conexao)
    repo = RepositorioStagingSqlite(conexao)
    despachante = DespachanteOutbox(repo, lake)

    evento = EventoPublicacao(
        id_evento="EVT_BRONZE",
        tipo_evento="bronze_pagina",
        chave_origem="bronze/steam/pagina_1.json",
        payload_referencia='{"status": "ok"}',
        status_publicacao="pendente",
        tentativas=0,
        data_criacao=datetime.now(UTC),
    )

    with uow:
        repo.enfileirar_evento_outbox(evento)

    total_publicado = despachante.executar_ciclo_publicacao(limite_lote=10)
    assert total_publicado == 1
    assert "bronze/steam/pagina_1.json" in lake.textos
    assert lake.textos["bronze/steam/pagina_1.json"] == '{"status": "ok"}'

    # Staging deve constar 0 pendentes
    assert len(repo.obter_eventos_pendentes()) == 0
