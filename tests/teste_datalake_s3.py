"""Testes unitários para o RepositorioS3Lakehouse e camadas do Data Lakehouse remoto."""

import io

import pandas as pd
import pytest
from botocore.exceptions import ClientError
from botocore.response import StreamingBody

from app.conf_yaml import ConfigCamadaLake, ConfigDatalakeInfo
from app.excecoes import ErroDatalake
from app.gestao_datalake.repositorio_s3_lakehouse import RepositorioS3Lakehouse


class RespostaGetObjectFake:
    def __init__(self, corpo: bytes) -> None:
        self._corpo = corpo

    def __getitem__(self, item: str) -> StreamingBody:
        return StreamingBody(io.BytesIO(self._corpo), len(self._corpo))


class ClienteS3Fake:
    """Simulador de cliente S3 para testes unitários em memória."""

    def __init__(self) -> None:
        self.objetos: dict[tuple[str, str], bytes] = {}

    def put_object(self, **kwargs: object) -> dict[str, object]:
        bucket = str(kwargs["Bucket"])
        key = str(kwargs["Key"])
        body = kwargs["Body"]
        conteudo = bytes(body) if isinstance(body, (bytes, bytearray)) else body.read()  # type: ignore[union-attr]
        self.objetos[(bucket, key)] = conteudo
        return {"ETag": "fake-etag"}

    def get_object(self, **kwargs: object) -> RespostaGetObjectFake:
        bucket = str(kwargs["Bucket"])
        key = str(kwargs["Key"])
        if (bucket, key) not in self.objetos:
            raise ClientError(
                error_response={"Error": {"Code": "NoSuchKey", "Message": "Key not found"}},
                operation_name="GetObject",
            )
        conteudo = self.objetos[(bucket, key)]
        return RespostaGetObjectFake(conteudo)


def test_gravar_bronze_gera_parquet_no_s3() -> None:
    """Verifica que a gravação na camada Bronze gera objeto Parquet na chave particionada."""
    cliente_s3 = ClienteS3Fake()
    config = ConfigDatalakeInfo(
        bucket="test-bucket",
        bronze=ConfigCamadaLake(prefixo="bronze"),
    )
    repo = RepositorioS3Lakehouse(config=config, cliente_s3=cliente_s3)

    registros: list[dict[str, object]] = [{"id": 1, "review": "otimo"}, {"id": 2, "review": "ruim"}]
    uri = repo.gravar_bronze(identificador=730, registros=registros)

    assert uri.startswith("s3://test-bucket/bronze/730/ano=")
    assert uri.endswith(".parquet")

    # Verifica que o objeto foi inserido no cliente S3
    chaves = [k for (b, k) in cliente_s3.objetos if b == "test-bucket"]
    assert len(chaves) == 1
    assert "bronze/730" in chaves[0]


def test_gravar_e_ler_silver() -> None:
    """Verifica o ciclo completo de gravação e leitura na camada Silver."""
    cliente_s3 = ClienteS3Fake()
    config = ConfigDatalakeInfo(
        bucket="test-bucket",
        silver=ConfigCamadaLake(prefixo="silver"),
    )
    repo = RepositorioS3Lakehouse(config=config, cliente_s3=cliente_s3)

    df_original = pd.DataFrame(
        {
            "recommendationid": ["r1", "r2"],
            "votes_up": [10, 20],
            "voted_up": [True, False],
        }
    )

    uri = repo.gravar_silver(identificador=730, dados=df_original)
    assert uri == "s3://test-bucket/silver/730/dados.parquet"

    df_lido = repo.ler_silver(identificador=730)
    assert len(df_lido) == 2
    assert list(df_lido["recommendationid"]) == ["r1", "r2"]
    assert list(df_lido["votes_up"]) == [10, 20]
    assert list(df_lido["voted_up"]) == [True, False]


def test_gravar_e_ler_gold() -> None:
    """Verifica o ciclo de gravação e leitura na camada Gold com sufixo de visão."""
    cliente_s3 = ClienteS3Fake()
    config = ConfigDatalakeInfo(
        bucket="test-bucket",
        gold=ConfigCamadaLake(prefixo="gold"),
    )
    repo = RepositorioS3Lakehouse(config=config, cliente_s3=cliente_s3)

    df_matriz = pd.DataFrame(
        {
            "votes_up": [1.5, 2.5],
            "playtime_forever": [100.0, 200.0],
        }
    )

    uri = repo.gravar_gold(identificador=730, dados=df_matriz, sufixo_visao="matriz_treino")
    assert uri == "s3://test-bucket/gold/730/matriz_treino.parquet"

    df_lido = repo.ler_gold(identificador=730, sufixo_visao="matriz_treino")
    assert len(df_lido) == 2
    assert "votes_up" in df_lido.columns
    assert "playtime_forever" in df_lido.columns


def test_falha_leitura_dispara_erro_datalake() -> None:
    """Verifica lançamento de ErroDatalake quando a chave solicitada não existe."""
    cliente_s3 = ClienteS3Fake()
    config = ConfigDatalakeInfo(bucket="test-bucket")
    repo = RepositorioS3Lakehouse(config=config, cliente_s3=cliente_s3)

    with pytest.raises(ErroDatalake, match="Não foi possível ler camada Silver"):
        repo.ler_silver(identificador=999999)
