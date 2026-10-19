"""Adaptador de cliente S3/RustFS sem gravação em disco local."""

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from mypy_boto3_s3.client import S3Client


class ClienteS3Erro(Exception):
    """Exceção para falhas na comunicação com o serviço S3."""


class ClienteS3:
    """Encapsula operações S3 operando exclusivamente em memória RAM (BytesIO)."""

    def __init__(
        self,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region_name: str = "us-east-1",
        cliente_boto: S3Client | None = None,
    ) -> None:
        if cliente_boto is not None:
            self._s3: S3Client = cliente_boto
        else:
            config = Config(
                s3={"addressing_style": "path"},
                signature_version="s3v4",
            )
            cliente_criado = boto3.client(
                "s3",
                endpoint_url=endpoint_url or "http://127.0.0.1:9000",
                aws_access_key_id=access_key or "rustfs_admin",
                aws_secret_access_key=secret_key or "RustFS@2026Admin",
                region_name=region_name,
                config=config,
            )
            self._s3 = cliente_criado

    def garantir_bucket_existente(self, bucket: str) -> None:
        """Verifica se o bucket existe no storage e cria caso ausente."""
        try:
            self._s3.head_bucket(Bucket=bucket)
        except ClientError as erro:
            resposta_erro = erro.response
            codigo_erro = resposta_erro.get("Error", {}).get("Code")
            meta = resposta_erro.get("ResponseMetadata")
            status_http = meta.get("HTTPStatusCode") if isinstance(meta, dict) else None
            if codigo_erro in ("404", "NoSuchBucket", 404) or status_http == 404:
                try:
                    self._s3.create_bucket(Bucket=bucket)
                except Exception as erro_criacao:
                    raise ClienteS3Erro(
                        f"Falha ao criar bucket {bucket}: {erro_criacao}"
                    ) from erro_criacao
            else:
                raise ClienteS3Erro(
                    f"Erro ao verificar bucket {bucket}: {erro}"
                ) from erro
        except Exception as erro_geral:
            raise ClienteS3Erro(
                f"Falha de conexão com S3 ao validar bucket {bucket}: {erro_geral}"
            ) from erro_geral

    def enviar_bytes(
        self,
        bucket: str,
        chave: str,
        conteudo: bytes,
        tipo_conteudo: str = "application/octet-stream",
    ) -> None:
        """Envia bytes em memória para uma chave S3 sem tocar no disco."""
        try:
            self._s3.put_object(
                Bucket=bucket,
                Key=chave,
                Body=conteudo,
                ContentType=tipo_conteudo,
            )
        except Exception as erro:
            raise ClienteS3Erro(
                f"Erro ao enviar objeto para s3://{bucket}/{chave}: {erro}"
            ) from erro

    def baixar_bytes(self, bucket: str, chave: str) -> bytes:
        """Lê bytes de um objeto S3 diretamente em memória."""
        try:
            resposta = self._s3.get_object(Bucket=bucket, Key=chave)
            corpo = resposta["Body"]
            conteudo = corpo.read()
            return conteudo
        except Exception as erro:
            raise ClienteS3Erro(
                f"Erro ao baixar objeto s3://{bucket}/{chave}: {erro}"
            ) from erro

    def listar_chaves(self, bucket: str, prefixo: str) -> list[str]:
        """Lista todas as chaves existentes com determinado prefixo."""
        try:
            resposta = self._s3.list_objects_v2(Bucket=bucket, Prefix=prefixo)
            conteudos = resposta.get("Contents")
            if not isinstance(conteudos, list):
                return []
            chaves: list[str] = []
            for item in conteudos:
                chave_val = item.get("Key")
                if isinstance(chave_val, str):
                    chaves.append(chave_val)
            return sorted(chaves)
        except Exception as erro:
            raise ClienteS3Erro(
                f"Erro ao listar objetos com prefixo {prefixo} no bucket {bucket}: {erro}"
            ) from erro

    def listar_metadados_objetos(self, bucket: str, prefixo: str = "") -> list[tuple[str, int]]:
        """Retorna tuplas (chave, tamanho_bytes) para todos os objetos existentes com determinado prefixo."""
        try:
            resposta = self._s3.list_objects_v2(Bucket=bucket, Prefix=prefixo)
            conteudos = resposta.get("Contents")
            if not isinstance(conteudos, list):
                return []
            resultados: list[tuple[str, int]] = []
            for item in conteudos:
                chave_val = item.get("Key")
                tamanho_val = item.get("Size")
                if isinstance(chave_val, str) and isinstance(tamanho_val, (int, float)):
                    resultados.append((chave_val, int(tamanho_val)))
            return resultados
        except Exception:
            return []

