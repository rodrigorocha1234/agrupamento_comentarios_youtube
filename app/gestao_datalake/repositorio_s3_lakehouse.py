"""Implementação de repositório Lakehouse no RustFS/S3 com armazenamento em memória e sem I/O local."""

import io
import os
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol, override

import boto3
import pandas as pd

from app.conf_yaml import ConfigDatalakeInfo
from app.contratos.repositorio import ProtocoloRepositorioLakehouse
from app.excecoes import ErroDatalake


class ProtocoloCorpoS3(Protocol):
    def read(self) -> bytes: ...


class ProtocoloRespostaGetObject(Protocol):
    def __getitem__(self, item: str) -> ProtocoloCorpoS3: ...


class ProtocoloClienteS3(Protocol):
    """Protocolo estrito para chamadas de cliente S3."""

    def put_object(self, **kwargs: object) -> object: ...
    def get_object(self, **kwargs: object) -> ProtocoloRespostaGetObject: ...


class RepositorioS3Lakehouse(ProtocoloRepositorioLakehouse):
    """Gerencia as camadas Bronze, Silver e Gold diretamente no RustFS/S3 remoto."""

    def __init__(
        self,
        config: ConfigDatalakeInfo,
        cliente_s3: ProtocoloClienteS3 | None = None,
    ) -> None:
        self._config = config
        self._bucket = config.bucket
        self._prefixo_bronze = config.bronze.prefixo.strip("/")
        self._prefixo_silver = config.silver.prefixo.strip("/")
        self._prefixo_gold = config.gold.prefixo.strip("/")

        if cliente_s3 is not None:
            self._s3 = cliente_s3
        else:
            endpoint_url = config.endpoint_url
            aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID", "admin")
            aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "admin12345")
            regiao = config.regiao

            self._s3 = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=regiao,
            )  # type: ignore[assignment]

    @override
    def gravar_bronze(
        self,
        identificador: str | int,
        registros: Sequence[dict[str, object]],
    ) -> str:
        """Persiste registros brutos da ingestão na camada Bronze no RustFS/S3."""
        if not registros:
            return ""

        agora = datetime.now(UTC)
        chave_s3 = (
            f"{self._prefixo_bronze}/{identificador}/ano={agora.year:04d}/"
            f"mes={agora.month:02d}/dia={agora.day:02d}/lote_{int(agora.timestamp())}.parquet"
        )

        try:
            df = pd.DataFrame(registros)
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False, engine="pyarrow")
            buffer.seek(0)

            self._s3.put_object(
                Bucket=self._bucket,
                Key=chave_s3,
                Body=buffer.getvalue(),
                ContentType="application/x-parquet",
            )
            return f"s3://{self._bucket}/{chave_s3}"
        except Exception as exc:
            raise ErroDatalake(
                f"Falha ao gravar lote na camada Bronze ({chave_s3}): {exc}"
            ) from exc

    @override
    def gravar_silver(
        self,
        identificador: str | int,
        dados: pd.DataFrame,
    ) -> str:
        """Persiste dados higienizados e estruturados na camada Silver no RustFS/S3."""
        chave_s3 = f"{self._prefixo_silver}/{identificador}/dados.parquet"
        try:
            buffer = io.BytesIO()
            dados.to_parquet(buffer, index=False, engine="pyarrow")
            buffer.seek(0)

            self._s3.put_object(
                Bucket=self._bucket,
                Key=chave_s3,
                Body=buffer.getvalue(),
                ContentType="application/x-parquet",
            )
            return f"s3://{self._bucket}/{chave_s3}"
        except Exception as exc:
            raise ErroDatalake(
                f"Falha ao gravar dados na camada Silver ({chave_s3}): {exc}"
            ) from exc

    @override
    def gravar_gold(
        self,
        identificador: str | int,
        dados: pd.DataFrame,
        sufixo_visao: str,
    ) -> str:
        """Persiste matrizes de atributos analíticos na camada Gold no RustFS/S3."""
        chave_s3 = f"{self._prefixo_gold}/{identificador}/{sufixo_visao}.parquet"
        try:
            buffer = io.BytesIO()
            dados.to_parquet(buffer, index=False, engine="pyarrow")
            buffer.seek(0)

            self._s3.put_object(
                Bucket=self._bucket,
                Key=chave_s3,
                Body=buffer.getvalue(),
                ContentType="application/x-parquet",
            )
            return f"s3://{self._bucket}/{chave_s3}"
        except Exception as exc:
            raise ErroDatalake(
                f"Falha ao gravar visão Gold ({chave_s3}): {exc}"
            ) from exc

    @override
    def ler_silver(self, identificador: str | int) -> pd.DataFrame:
        """Lê os dados da camada Silver para o identificador a partir do RustFS/S3."""
        chave_s3 = f"{self._prefixo_silver}/{identificador}/dados.parquet"
        try:
            resposta = self._s3.get_object(Bucket=self._bucket, Key=chave_s3)
            corpo = resposta["Body"].read()
            buffer = io.BytesIO(corpo)
            return pd.read_parquet(buffer, engine="pyarrow")
        except Exception as exc:
            raise ErroDatalake(
                f"Não foi possível ler camada Silver ({chave_s3}) do RustFS/S3: {exc}"
            ) from exc

    @override
    def ler_gold(self, identificador: str | int, sufixo_visao: str) -> pd.DataFrame:
        """Lê visão analítica da camada Gold a partir do RustFS/S3."""
        chave_s3 = f"{self._prefixo_gold}/{identificador}/{sufixo_visao}.parquet"
        try:
            resposta = self._s3.get_object(Bucket=self._bucket, Key=chave_s3)
            corpo = resposta["Body"].read()
            buffer = io.BytesIO(corpo)
            return pd.read_parquet(buffer, engine="pyarrow")
        except Exception as exc:
            raise ErroDatalake(
                f"Não foi possível ler visão Gold ({chave_s3}) do RustFS/S3: {exc}"
            ) from exc
