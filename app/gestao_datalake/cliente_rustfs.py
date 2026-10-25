"""Adaptador de armazenamento em S3 / RustFS para persistência das camadas do Data Lake."""

import os
from typing import final, override

import boto3
from botocore.exceptions import ClientError

from app.dominio_contratos.protocolos_datalake import ArmazenamentoLake


@final
class ClienteRustfsS3(ArmazenamentoLake):
    """Conector boto3 compatível com S3/RustFS implementando ArmazenamentoLake."""

    def __init__(
        self,
        bucket: str = "steam-reviews",
        endpoint_url: str | None = None,
        regiao: str = "us-east-1",
        access_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        self._bucket = bucket
        self._endpoint = endpoint_url or os.getenv(
            "S3_ENDPOINT_URL", "http://127.0.0.1:9000"
        )
        self._regiao = regiao or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self._access_key = access_key or os.getenv("AWS_ACCESS_KEY_ID", "rustfs_admin")
        self._secret_key = secret_key or os.getenv(
            "AWS_SECRET_ACCESS_KEY", "RustFS@2026Admin"
        )

        self._cliente = boto3.client(
            "s3",
            endpoint_url=self._endpoint,
            region_name=self._regiao,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
        )
        self.garantir_bucket()

    def garantir_bucket(self) -> None:
        """Garante que o bucket alvo exista no storage, criando-o se necessário."""
        try:
            self._cliente.head_bucket(Bucket=self._bucket)
        except (ClientError, OSError):
            try:
                self._cliente.create_bucket(Bucket=self._bucket)
            except (ClientError, OSError):
                pass

    @property
    def bucket(self) -> str:
        """Nome do bucket ativo."""
        return self._bucket

    @override
    def gravar_texto(self, caminho_chave: str, conteudo: str) -> None:
        """Envia string codificada em UTF-8 para o caminho S3 especificado."""
        self._cliente.put_object(
            Bucket=self._bucket,
            Key=caminho_chave.lstrip("/"),
            Body=conteudo.encode("utf-8"),
            ContentType="application/json",
        )

    @override
    def gravar_bytes(self, caminho_chave: str, dados_bytes: bytes) -> None:
        """Envia carga binária (ex: Parquet) para o caminho S3 especificado."""
        self._cliente.put_object(
            Bucket=self._bucket,
            Key=caminho_chave.lstrip("/"),
            Body=dados_bytes,
            ContentType="application/octet-stream",
        )

    @override
    def ler_bytes(self, caminho_chave: str) -> bytes:
        """Recupera conteúdo binário de um objeto no bucket S3/RustFS."""
        resposta = self._cliente.get_object(
            Bucket=self._bucket,
            Key=caminho_chave.lstrip("/"),
        )
        corpo = resposta["Body"]
        return corpo.read()

    @override
    def listar_chaves(self, prefixo: str) -> list[str]:
        """Lista as chaves de objetos sob o prefixo especificado no bucket."""
        chaves: list[str] = []
        try:
            paginador = self._cliente.get_paginator("list_objects_v2")
            for pagina in paginador.paginate(
                Bucket=self._bucket,
                Prefix=prefixo.lstrip("/"),
            ):
                itens = pagina.get("Contents", [])
                for item in itens:
                    chave = item.get("Key")
                    if isinstance(chave, str):
                        chaves.append(chave)
        except (ClientError, OSError):
            return []
        return chaves

    @override
    def verificar_existencia(self, caminho_chave: str) -> bool:
        """Verifica se a chave já existe no bucket."""
        try:
            self._cliente.head_object(
                Bucket=self._bucket,
                Key=caminho_chave.lstrip("/"),
            )
            return True
        except ClientError:
            return False
