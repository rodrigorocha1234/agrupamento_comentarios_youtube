"""Testes unitários e de integração para o OrquestradorPrincipal e Fábrica de Extração GoF."""

import io
from collections.abc import Iterator

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from app.dominio_contratos.modelos_dados import PaginaReviews
from app.dominio_contratos.protocolos_extracao import GeradorPaginas
from app.extracao_steam.fabrica_extracao import (
    ErroProvedorExtracaoNaoRegistrado,
    FabricaExtracao,
)
from app.orquestracao_pipeline.orquestrador_principal import OrquestradorPrincipal
from tests.teste_datalake import ArmazenamentoLakeFalso


class GeradorMock(GeradorPaginas):
    """Implementação mock para testar a injeção desacoplada de geradores."""

    def __init__(self, paginas: list[PaginaReviews]) -> None:
        self._paginas = paginas

    def iterar_paginas(
        self, appid: int, cursor_inicial: str = "*"
    ) -> Iterator[PaginaReviews]:
        yield from self._paginas


def teste_orquestrador_falha_quando_particao_silver_inexistente() -> None:
    """Garante que a ausência de dados no bucket lança FileNotFoundError sem gerar dados sintéticos."""
    orquestrador = OrquestradorPrincipal()

    with pytest.raises(FileNotFoundError) as exc_info:
        orquestrador.obter_dados_silver(appid=999999)

    assert "Nenhum dado encontrado na partição Silver para o AppID 999999" in str(
        exc_info.value
    )


def teste_orquestrador_recupera_silver_do_bucket(monkeypatch: pytest.MonkeyPatch) -> None:
    """Garante que obter_dados_silver carrega registros reais gravados no bucket S3/Lakehouse."""
    appid = 730
    lake_falso = ArmazenamentoLakeFalso()

    tabela = pa.Table.from_pydict(
        {
            "appid": [appid, appid],
            "recommendationid": ["REC_001", "REC_002"],
            "steamid": ["76561198000000001", "76561198000000002"],
            "voted_up": [True, False],
            "playtime_forever": [1500.0, 3200.0],
            "playtime_last_two_weeks": [50.0, 120.0],
            "playtime_at_review": [1200.0, 3000.0],
            "num_games_owned": [45, 120],
            "num_reviews": [3, 12],
            "comment_count": [1, 0],
            "language": ["brazilian", "brazilian"],
        }
    )
    buffer = io.BytesIO()
    pq.write_table(tabela, buffer)
    bytes_parquet = buffer.getvalue()

    chave_parquet = f"silver/steam/reviews/appid={appid}/ano=2026/mes=10/lote_001.parquet"
    lake_falso.gravar_bytes(chave_parquet, bytes_parquet)

    orquestrador = OrquestradorPrincipal(armazenamento_lake=lake_falso)
    df_silver = orquestrador.obter_dados_silver(appid=appid)

    assert len(df_silver) == 2
    assert list(df_silver["recommendationid"]) == ["REC_001", "REC_002"]
    assert df_silver["playtime_forever"].iloc[0] == 1500.0
    assert df_silver["playtime_forever"].iloc[1] == 3200.0


def teste_fabrica_extracao_registro_e_resolucao() -> None:
    """Valida a resolução desacoplada da fábrica GoF para clientes da Steam."""
    fabrica = FabricaExtracao()

    # Provedor padrão
    gerador_padrao = fabrica.criar_gerador("web_api", limite_paginas=2)
    assert hasattr(gerador_padrao, "iterar_paginas")

    # Registro de novo provedor customizado (OCP / Strategy)
    def _criador_mock(limite: int, tamanho: int) -> GeradorPaginas:
        return GeradorMock(paginas=[])

    fabrica.registrar_provedor("api_mock_v2", _criador_mock)
    gerador_customizado = fabrica.criar_gerador("api_mock_v2")
    assert isinstance(gerador_customizado, GeradorMock)


def teste_fabrica_extracao_rejeita_provedor_inexistente() -> None:
    """Garante que provedor desconhecido lance exceção formal sem fallback silencioso."""
    fabrica = FabricaExtracao()
    with pytest.raises(ErroProvedorExtracaoNaoRegistrado) as exc:
        fabrica.criar_gerador("api_inexistente_123")
    assert "não foi registrado" in str(exc.value)


def teste_orquestrador_coleta_com_fabricas_injetadas() -> None:
    """Valida o desacoplamento de banco e API no fluxo de coleta do OrquestradorPrincipal."""
    lake_falso = ArmazenamentoLakeFalso()
    fabrica_extracao = FabricaExtracao()

    fabrica_extracao.registrar_provedor(
        "mock_vazio",
        lambda limite, tamanho: GeradorMock(paginas=[]),
    )

    orquestrador = OrquestradorPrincipal(
        fabrica_extracao=fabrica_extracao,
        armazenamento_lake=lake_falso,
    )

    # Executa a coleta com banco SQLite e provedor de extração customizado
    orquestrador.executar_fluxo_coleta(
        appid=427520,
        tipo_banco="sqlite",
        tipo_api="mock_vazio",
        limite_paginas=1,
    )
