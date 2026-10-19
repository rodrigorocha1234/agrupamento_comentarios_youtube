"""Script utilitário para limpeza recursiva de camadas e objetos no RustFS/S3."""

import argparse
import os
import sys
import boto3
from botocore.client import Config


def obter_cliente_s3() -> boto3.client: # type: ignore
    endpoint = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "rustfs_admin")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "RustFS@2026Admin")
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name=region,
    )


def limpar_prefixo(cliente: boto3.client, bucket: str, prefixo: str) -> int: # type: ignore
    """Remove recursivamente todos os objetos sob um prefixo virtual no S3."""
    paginador = cliente.get_paginator("list_objects_v2")
    total_deletados = 0

    print(f"Buscando objetos em s3://{bucket}/{prefixo}...")
    for pagina in paginador.paginate(Bucket=bucket, Prefix=prefixo):
        objetos = pagina.get("Contents", [])
        if not objetos:
            continue

        lote = [{"Key": obj["Key"]} for obj in objetos if "Key" in obj]
        if lote:
            resp = cliente.delete_objects(Bucket=bucket, Delete={"Objects": lote})
            deletados = len(resp.get("Deleted", []))
            total_deletados += deletados
            for item in resp.get("Deleted", []):
                print(f"  [DELETADO] {item.get('Key')}")

    return total_deletados


def main() -> None:
    parser = argparse.ArgumentParser(description="Limpeza recursiva de camadas do Data Lakehouse no S3/RustFS.")
    parser.add_argument(
        "--bucket",
        type=str,
        default="youtube-comentarios",
        help="Nome do bucket S3 alvo (padrão: youtube-comentarios)",
    )
    parser.add_argument(
        "--camada",
        type=str,
        choices=["bronze", "prata", "ouro", "todas"],
        default="todas",
        help="Camada a ser limpa: bronze, prata, ouro ou todas (padrão: todas)",
    )
    parser.add_argument(
        "--confirmar",
        action="store_true",
        help="Executa a exclusão de fato (sem dry-run)",
    )

    args = parser.parse_args()
    cliente = obter_cliente_s3()

    camadas = ["bronze/", "prata/", "ouro/"] if args.camada == "todas" else [f"{args.camada}/"]

    if not args.confirmar:
        print("MODO DE SIMULAÇÃO (DRY-RUN): Adicione a flag --confirmar para executar a exclusão.")
        for cam in camadas:
            resp = cliente.list_objects_v2(Bucket=args.bucket, Prefix=cam)
            itens = resp.get("Contents", [])
            print(f"- Camada {cam}: {len(itens)} objetos encontrados.")
        sys.exit(0)

    print(f"Iniciando exclusão recursiva no bucket '{args.bucket}'...")
    total = 0
    for cam in camadas:
        removidos = limpar_prefixo(cliente, args.bucket, cam)
        print(f"Camada '{cam}': {removidos} objetos excluídos com sucesso.")
        total += removidos

    print(f"\nConcluído! Total de {total} objetos excluídos do Lakehouse.")


if __name__ == "__main__":
    main()
