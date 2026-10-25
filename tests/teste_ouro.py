"""Testes automatizados para persistência na camada Gold do Data Lake."""

import io
from typing import final, override

import pandas as pd
import pyarrow.parquet as pq

from app.avaliacao_modelos.metricas_estatisticas import ResultadoAvaliacao
from app.dominio_contratos.protocolos_datalake import ArmazenamentoLake
from app.gestao_datalake.escritor_ouro import EscritorCamadaOuro


@final
class ArmazenamentoLakeFalso(ArmazenamentoLake):
    """Implementação em memória de ArmazenamentoLake para testes da camada Gold."""

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


def teste_escritor_ouro_salvar_clusters() -> None:
    """Verifica a serialização colunar Parquet de clusters na camada Gold."""
    lake = ArmazenamentoLakeFalso()
    escritor = EscritorCamadaOuro(lake)

    df_clusters = pd.DataFrame(
        {
            "recommendationid": ["101", "102", "103"],
            "cluster_id": [0, 1, -1],
            "rotulo_negocio": [
                "veteranos_leais",
                "novatos_satisfeitos",
                "ruido_outliers",
            ],
            "playtime_forever": [12000, 450, 80],
            "votes_up": [15, 2, 0],
        }
    )

    caminho = escritor.salvar_dataset_clusters(
        appid=427520,
        nome_modelo="kmeans",
        versao="v1_teste",
        df=df_clusters,
    )

    assert caminho in lake.arquivos_binarios
    conteudo_bytes = lake.arquivos_binarios[caminho]
    assert len(conteudo_bytes) > 0

    tabela_lida = pq.read_table(io.BytesIO(conteudo_bytes))
    df_lido = tabela_lida.to_pandas()
    assert len(df_lido) == 3
    assert list(df_lido["cluster_id"]) == [0, 1, -1]
    assert list(df_lido["rotulo_negocio"]) == [
        "veteranos_leais",
        "novatos_satisfeitos",
        "ruido_outliers",
    ]


def teste_escritor_ouro_salvar_metricas() -> None:
    """Verifica persistência de métricas estatísticas em Parquet na camada Gold."""
    lake = ArmazenamentoLakeFalso()
    escritor = EscritorCamadaOuro(lake)

    avaliacao = ResultadoAvaliacao(
        total_amostras=500,
        total_clusters=3,
        total_ruido=15,
        proporcao_ruido=0.03,
        silhouette_global=0.55,
        silhouette_sem_ruido=0.58,
        davies_bouldin=0.82,
        calinski_harabasz=145.2,
        tamanhos_clusters={0: 250, 1: 150, 2: 85, -1: 15},
    )

    caminho = escritor.salvar_metricas(
        appid=427520,
        versao="v1_metricas",
        avaliacao=avaliacao,
    )

    assert caminho in lake.arquivos_binarios
    tabela_lida = pq.read_table(io.BytesIO(lake.arquivos_binarios[caminho]))
    df_lido = tabela_lida.to_pandas()

    assert len(df_lido) == 1
    assert int(df_lido["total_amostras"].iloc[0]) == 500
    assert float(df_lido["silhouette_global"].iloc[0]) == 0.55


def teste_escritor_ouro_salvar_resumo_e_manifesto() -> None:
    """Verifica persistência de resumo JSON e manifesto analítico na camada Gold."""
    lake = ArmazenamentoLakeFalso()
    escritor = EscritorCamadaOuro(lake)

    resumo = '{"modelo": "kmeans", "status": "sucesso"}'
    caminho_resumo = escritor.salvar_resumo_executivo(
        appid=427520,
        versao="v1",
        resumo_json=resumo,
    )
    assert caminho_resumo in lake.textos
    assert lake.textos[caminho_resumo] == resumo

    manifesto = {
        "appid": 427520,
        "hash_execucao": "abc123sha256",
        "modelo": "kmeans",
        "total_registros": 500,
    }
    caminho_manifesto = escritor.salvar_manifesto_ouro(
        appid=427520,
        versao="v1",
        manifesto_dados=manifesto,
    )
    assert caminho_manifesto in lake.textos
    assert "abc123sha256" in lake.textos[caminho_manifesto]
