"""Gestão da camada Bronze (dados brutos particionados em JSONL)."""

from datetime import datetime, timezone
import json
import time
from typing import cast
import uuid

from app.coleta_metricas.medidor_datalake import MedidorDatalake
from app.coleta_youtube.modelos_coleta import ComentarioColetado
from app.configuracao_geral.tipos_enumerados import CamadaLakehouse
from app.gestao_dados.cliente_s3 import ClienteS3


class CamadaBronze:
    """Gerencia a gravação e leitura de histórico imutável na camada Bronze do S3."""

    def __init__(
        self,
        cliente_s3: ClienteS3,
        bucket: str,
        prefixo_bronze: CamadaLakehouse | str = CamadaLakehouse.BRONZE,
        padrao_chave: str | None = None,
    ) -> None:
        self._s3: ClienteS3 = cliente_s3
        self._bucket: str = bucket
        self._prefixo: str = str(prefixo_bronze)
        self._padrao_chave: str = padrao_chave or (
            "{prefixo}/id_canal={id_canal}/id_video={id_video}/"
            "data_coleta={data_coleta}/lote={id_lote}.jsonl"
        )

    def gravar_lote_comentarios(
        self,
        id_canal: str,
        id_video: str,
        comentarios: list[ComentarioColetado],
    ) -> str:
        """Serializa os comentários em JSONL na memória e grava no S3 de forma particionada."""
        data_coleta = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        id_lote = str(uuid.uuid4())
        chave = self._padrao_chave.format(
            prefixo=self._prefixo,
            id_canal=id_canal,
            id_video=id_video,
            data_coleta=data_coleta,
            id_lote=id_lote,
        )

        linhas: list[str] = []
        for com in comentarios:
            registro = {
                "id_comentario": com.id_comentario,
                "id_video": com.id_video,
                "id_canal": com.id_canal,
                "id_comentario_pai": com.id_comentario_pai,
                "etag": com.etag,
                "texto_original": com.texto_original,
                "hash_conteudo": com.hash_conteudo,
                "publicado_em": com.publicado_em.isoformat(),
                "atualizado_em": com.atualizado_em.isoformat(),
                "contagem_curtidas": com.contagem_curtidas,
                "origem": com.origem,
                "coletado_em": com.coletado_em.isoformat(),
            }
            linhas.append(json.dumps(registro, ensure_ascii=False))

        conteudo_bytes = "\n".join(linhas).encode("utf-8")
        inicio = time.perf_counter()
        self._s3.enviar_bytes(
            bucket=self._bucket,
            chave=chave,
            conteudo=conteudo_bytes,
            tipo_conteudo="application/x-ndjson",
        )
        duracao = time.perf_counter() - inicio
        MedidorDatalake.registrar_gravacao(
            camada="bronze",
            formato="jsonl",
            quantidade_bytes=len(conteudo_bytes),
            quantidade_registros=len(comentarios),
            duracao_segundos=duracao,
        )
        return chave

    def carregar_comentarios_lote(self, chave: str) -> list[ComentarioColetado]:
        """Lê os bytes da chave S3 e desserializa em instâncias tipadas."""
        inicio = time.perf_counter()
        conteudo_bytes = self._s3.baixar_bytes(bucket=self._bucket, chave=chave)
        duracao = time.perf_counter() - inicio
        MedidorDatalake.registrar_leitura(
            camada="bronze",
            quantidade_bytes=len(conteudo_bytes),
            duracao_segundos=duracao,
        )
        texto = conteudo_bytes.decode("utf-8")
        comentarios: list[ComentarioColetado] = []

        for linha in texto.splitlines():
            if not linha.strip():
                continue
            item_raw: object = json.loads(linha)
            if not isinstance(item_raw, dict):
                continue
            item = cast(dict[str, object], item_raw)

            id_pai_raw = item.get("id_comentario_pai")
            id_pai = str(id_pai_raw) if id_pai_raw is not None else None

            comentarios.append(
                ComentarioColetado(
                    id_comentario=str(item.get("id_comentario", "")),
                    id_video=str(item.get("id_video", "")),
                    id_canal=str(item.get("id_canal", "")),
                    id_comentario_pai=id_pai,
                    etag=str(item.get("etag", "")),
                    texto_original=str(item.get("texto_original", "")),
                    hash_conteudo=str(item.get("hash_conteudo", "")),
                    publicado_em=datetime.fromisoformat(str(item.get("publicado_em", ""))),
                    atualizado_em=datetime.fromisoformat(str(item.get("atualizado_em", ""))),
                    contagem_curtidas=int(str(item.get("contagem_curtidas", 0))),
                    origem=str(item.get("origem", "principal")),
                    coletado_em=datetime.fromisoformat(str(item.get("coletado_em", ""))),
                )
            )

        return comentarios
