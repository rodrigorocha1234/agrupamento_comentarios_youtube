"""Testes unitários para a camada de ingestão de fontes desacopladas."""

import sqlite3
from collections.abc import Sequence
from typing import cast, override

import httpx
import pandas as pd
import pytest

from app.conf_yaml import (
    ConfigAPIRestInfo,
    ConfigBancoDadosInfo,
    ConfigFonteDados,
    ConfigFonteInfo,
)
from app.contratos.fonte_dados import ProtocoloFonteDados
from app.contratos.repositorio import ProtocoloRepositorioLakehouse
from app.contratos.tipos_dados import RegistroDado
from app.excecoes import ErroConexaoFonte
from app.extracao_steam.cliente_steam_api import ClienteSteamAPI
from app.extracao_steam.coletor_steam import ColetorSteam
from app.ingestao_fontes.adaptadores.adaptador_api_rest import AdaptadorAPIRest
from app.ingestao_fontes.adaptadores.adaptador_banco_dados import (
    AdaptadorBancoDados,
    ProtocoloConexaoDB,
)
from app.ingestao_fontes.adaptadores.adaptador_steam import AdaptadorSteam
from app.ingestao_fontes.cliente_http_resiliente import ClienteHTTPResiliente
from app.ingestao_fontes.coletor_dados import ColetorDados
from app.ingestao_fontes.fabrica_fontes import FabricaFontes


class RepositorioEmMemoriaFake(ProtocoloRepositorioLakehouse):
    """Implementação em memória do repositório para isolamento completo em testes."""

    def __init__(self) -> None:
        self.bronze_lotes: list[tuple[str | int, Sequence[RegistroDado]]] = []
        self.silver_dados: dict[str | int, pd.DataFrame] = {}
        self.gold_dados: dict[str, pd.DataFrame] = {}

    @override
    def gravar_bronze(self, identificador: str | int, registros: Sequence[RegistroDado]) -> str:
        self.bronze_lotes.append((identificador, registros))
        return f"s3://fake-bucket/bronze/{identificador}/lote.parquet"

    @override
    def gravar_silver(self, identificador: str | int, dados: pd.DataFrame) -> str:
        self.silver_dados[identificador] = dados.copy()
        return f"s3://fake-bucket/silver/{identificador}/dados.parquet"

    @override
    def gravar_gold(self, identificador: str | int, dados: pd.DataFrame, sufixo_visao: str) -> str:
        self.gold_dados[f"{identificador}/{sufixo_visao}"] = dados.copy()
        return f"s3://fake-bucket/gold/{identificador}/{sufixo_visao}.parquet"

    @override
    def ler_bronze(self, identificador: str | int) -> pd.DataFrame:
        registros: list[RegistroDado] = []
        for id_lote, lote in self.bronze_lotes:
            if id_lote == identificador:
                registros.extend(lote)
        return pd.DataFrame(registros) if registros else pd.DataFrame()

    @override
    def ler_silver(self, identificador: str | int) -> pd.DataFrame:
        if identificador in self.silver_dados:
            return self.silver_dados[identificador]
        return pd.DataFrame()

    @override
    def ler_gold(self, identificador: str | int, sufixo_visao: str) -> pd.DataFrame:
        chave = f"{identificador}/{sufixo_visao}"
        if chave in self.gold_dados:
            return self.gold_dados[chave]
        return pd.DataFrame()


def test_cliente_http_sucesso() -> None:
    """Verifica que o cliente HTTP executa requisição com sucesso."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok", "items": [1, 2, 3]})

    transporte = httpx.MockTransport(handler)
    cliente_httpx = httpx.Client(transport=transporte)
    cliente = ClienteHTTPResiliente(cliente_httpx=cliente_httpx)

    dados = cliente.requisitar_json("GET", "https://api.exemplo.com/dados")
    assert dados["status"] == "ok"
    assert dados["items"] == [1, 2, 3]


def test_cliente_http_retry_com_recuperacao() -> None:
    """Garante que falhas temporárias 500 disparam retry e recuperam em sucesso subsequente."""
    tentativas = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal tentativas
        tentativas += 1
        if tentativas < 3:
            return httpx.Response(500, text="Erro temporário no servidor")
        return httpx.Response(200, json={"sucesso": True})

    transporte = httpx.MockTransport(handler)
    cliente_httpx = httpx.Client(transport=transporte)
    cliente = ClienteHTTPResiliente(
        cliente_httpx=cliente_httpx,
        tentativas_maximas=4,
        espera_base_segundos=0.01,
    )

    dados = cliente.requisitar_json("GET", "https://api.exemplo.com/teste")
    assert dados["sucesso"] is True
    assert tentativas == 3


def test_cliente_http_esgota_tentativas_e_lanca_excecao() -> None:
    """Verifica lançamento de ErroConexaoFonte quando todas as tentativas falham."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Serviço indisponível")

    transporte = httpx.MockTransport(handler)
    cliente_httpx = httpx.Client(transport=transporte)
    cliente = ClienteHTTPResiliente(
        cliente_httpx=cliente_httpx,
        tentativas_maximas=2,
        espera_base_segundos=0.01,
    )

    with pytest.raises(ErroConexaoFonte, match="Falha após 2 tentativas"):
        cliente.requisitar_json("GET", "https://api.exemplo.com/falha")


def test_adaptador_steam_extracao_e_achatamento() -> None:
    """Verifica a extração e o achatamento dos atributos aninhados de 'author' na Steam API."""
    def handler(request: httpx.Request) -> httpx.Response:
        corpo = {
            "success": 1,
            "cursor": "cursor_pagina_2",
            "reviews": [
                {
                    "recommendationid": "123456",
                    "review": "Jogo excelente!",
                    "voted_up": True,
                    "votes_up": 10,
                    "votes_funny": 2,
                    "weighted_vote_score": 0.85,
                    "comment_count": 0,
                    "author": {
                        "steamid": "76561198000000001",
                        "num_games_owned": 50,
                        "num_reviews": 5,
                        "playtime_forever": 1200,
                        "playtime_last_two_weeks": 60,
                        "playtime_at_review": 1000,
                        "last_played": 1600000000,
                    },
                }
            ],
        }
        return httpx.Response(200, json=corpo)

    transporte = httpx.MockTransport(handler)
    cliente = ClienteHTTPResiliente(cliente_httpx=httpx.Client(transport=transporte))
    adaptador = AdaptadorSteam(cliente_http=cliente)

    registros, proximo_cursor, tem_mais = adaptador.extrair_lote(
        identificador_origem=730,
        marcador_posicao="*",
        limite=10,
    )

    assert len(registros) == 1
    assert registros[0]["recommendationid"] == "123456"
    assert registros[0]["steamid"] == "76561198000000001"
    assert registros[0]["playtime_forever"] == 1200
    assert registros[0]["appid"] == 730
    assert proximo_cursor == "cursor_pagina_2"
    assert tem_mais is True


def test_adaptador_api_rest() -> None:
    """Verifica o funcionamento do AdaptadorAPIRest genérico."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "itens": [
                    {"id": "comentario_1", "texto": "Primeiro", "likes": 5},
                    {"id": "comentario_2", "texto": "Segundo", "likes": 12},
                ],
                "proximo_cursor": "token_proxima_pagina",
            },
        )

    transporte = httpx.MockTransport(handler)
    cliente = ClienteHTTPResiliente(cliente_httpx=httpx.Client(transport=transporte))
    adaptador = AdaptadorAPIRest(
        cliente_http=cliente,
        endpoint="https://api.exemplo.com/videos/{identificador}/comentarios",
    )

    registros, prox_cursor, tem_mais = adaptador.extrair_lote(
        identificador_origem="video_abc",
        marcador_posicao=None,
        limite=50,
    )

    assert len(registros) == 2
    assert registros[0]["id"] == "comentario_1"
    assert prox_cursor == "token_proxima_pagina"
    assert tem_mais is True


def test_adaptador_banco_dados_sqlite() -> None:
    """Verifica o AdaptadorBancoDados com banco em memória paginado via offset."""
    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    cur.execute("CREATE TABLE reviews (id INTEGER PRIMARY KEY, autor TEXT, nota REAL)")
    cur.executemany(
        "INSERT INTO reviews (id, autor, nota) VALUES (?, ?, ?)",
        [(1, "Jogador A", 9.5), (2, "Jogador B", 8.0), (3, "Jogador C", 7.5)],
    )
    con.commit()

    adaptador = AdaptadorBancoDados(
        dsn="sqlite:///:memory:",
        tabela_ou_consulta="reviews",
        coluna_chave="id",
        conector=lambda _dsn: cast(ProtocoloConexaoDB, con),
    )

    lote1, marcador1, tem_mais1 = adaptador.extrair_lote(identificador_origem="tabela", limite=2)
    assert len(lote1) == 2
    assert lote1[0]["autor"] == "Jogador A"
    assert marcador1 == "2"
    assert tem_mais1 is True

    lote2, _marcador2, tem_mais2 = adaptador.extrair_lote(
        identificador_origem="tabela", marcador_posicao=marcador1, limite=2
    )
    assert len(lote2) == 1
    assert lote2[0]["autor"] == "Jogador C"
    assert tem_mais2 is False


def test_fabrica_fontes() -> None:
    """Verifica a resolução dinâmica de estratégias pela FabricaFontes."""
    # 1. Steam
    conf_steam = ConfigFonteDados(fonte=ConfigFonteInfo(tipo="steam_api"))
    fonte_steam = FabricaFontes.criar_fonte(conf_steam)
    assert isinstance(fonte_steam, AdaptadorSteam)

    # 2. Banco de Dados
    conf_banco = ConfigFonteDados(
        fonte=ConfigFonteInfo(
            tipo="banco_dados",
            banco_dados=ConfigBancoDadosInfo(dsn="sqlite:///:memory:", consulta_ou_tabela="tabela"),
        )
    )
    fonte_banco = FabricaFontes.criar_fonte(conf_banco)
    assert isinstance(fonte_banco, AdaptadorBancoDados)

    # 3. API REST
    conf_rest = ConfigFonteDados(
        fonte=ConfigFonteInfo(
            tipo="api_rest",
            api_rest=ConfigAPIRestInfo(endpoint="https://api.exemplo.com/recurso"),
        )
    )
    fonte_rest = FabricaFontes.criar_fonte(conf_rest)
    assert isinstance(fonte_rest, AdaptadorAPIRest)


def test_coletor_dados_orquestracao_e_deduplicacao() -> None:
    """Verifica o ciclo de coleta com deduplicação e gravação em Bronze e Silver."""
    chamadas = 0

    class FonteMock(ProtocoloFonteDados):
        @override
        def extrair_lote(
            self, identificador_origem: str | int, marcador_posicao: str | None = None, limite: int = 100
        ) -> tuple[list[RegistroDado], str | None, bool]:
            nonlocal chamadas
            chamadas += 1
            if chamadas == 1:
                return (
                    [
                        {"recommendationid": "rev_1", "votes_up": 10, "voted_up": True},
                        {"recommendationid": "rev_2", "votes_up": 5, "voted_up": False},
                    ],
                    "cursor_2",
                    True,
                )
            if chamadas == 2:
                # Retorna rev_2 duplicada e rev_3 nova
                return (
                    [
                        {"recommendationid": "rev_2", "votes_up": 5, "voted_up": False},
                        {"recommendationid": "rev_3", "votes_up": 20, "voted_up": True},
                    ],
                    "cursor_3",
                    False,
                )
            return [], None, False

        @override
        def coletar_lote(
            self, appid: int, cursor: str, quantidade_por_pagina: int
        ) -> tuple[list[RegistroDado], str, bool]:
            return [], "", False

    fonte = FonteMock()
    repo = RepositorioEmMemoriaFake()
    coletor = ColetorDados(fonte=fonte, repositorio=repo, campo_deduplicacao="recommendationid")

    relatorio = coletor.executar_coleta(
        identificador_origem=730,
        limite_total_registros=10,
        tamanho_lote=2,
        pausa_entre_lotes_segundos=0.0,
    )

    assert relatorio["total_coletado"] == 3  # rev_1, rev_2, rev_3 (rev_2 duplicada descartada)
    assert relatorio["duplicatas_ignoradas"] == 1
    assert relatorio["lotes_bronze_gravados"] == 2
    assert 730 in repo.silver_dados

    df_silver = repo.silver_dados[730]
    assert len(df_silver) == 3
    assert set(df_silver["recommendationid"]) == {"rev_1", "rev_2", "rev_3"}


def test_extracao_steam_compatibilidade() -> None:
    """Garante compatibilidade com as classes legadas ClienteSteamAPI e ColetorSteam."""
    cliente = ClienteSteamAPI()
    assert isinstance(cliente, AdaptadorSteam)

    repo = RepositorioEmMemoriaFake()
    coletor = ColetorSteam(fonte=cliente, repositorio=repo)
    assert isinstance(coletor, ColetorDados)
