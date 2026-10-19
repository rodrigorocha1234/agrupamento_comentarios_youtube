"""Gestão da camada Prata (comentários deduplicados e tipados em Parquet)."""

from datetime import datetime, timezone
import io
import time
from typing import cast
import pyarrow as pa
import pyarrow.parquet as pq

from app.coleta_metricas.medidor_datalake import MedidorDatalake
from app.coleta_youtube.modelos_coleta import ComentarioColetado
from app.configuracao_geral.tipos_enumerados import CamadaLakehouse
from app.gestao_dados.cliente_s3 import ClienteS3


class CamadaPrata:
    """Gerencia a persistência de snapshots deduplicados na camada Prata do S3."""

    def __init__(
        self,
        cliente_s3: ClienteS3,
        bucket: str,
        prefixo_prata: CamadaLakehouse | str = CamadaLakehouse.PRATA,
        padrao_chave: str | None = None,
    ) -> None:
        self._s3: ClienteS3 = cliente_s3
        self._bucket: str = bucket
        self._prefixo: str = str(prefixo_prata)
        self._padrao_chave: str = padrao_chave or (
            "{prefixo}/id_canal={id_canal}/id_video={id_video}/"
            "versao={timestamp_versao}/comentarios.parquet"
        )

    def gravar_snapshot_comentarios(
        self,
        id_canal: str,
        id_video: str,
        comentarios: list[ComentarioColetado],
        timestamp_versao: str | None = None,
    ) -> str:
        """Deduplica comentários por ID mantendo a versão mais recente e salva em Parquet no S3."""
        if not comentarios:
            return ""

        # Deduplicação determinística em memória
        ultimos_comentarios: dict[str, ComentarioColetado] = {}
        for com in comentarios:
            existente = ultimos_comentarios.get(com.id_comentario)
            if existente is None or com.atualizado_em >= existente.atualizado_em:
                ultimos_comentarios[com.id_comentario] = com

        comentarios_ordenados = sorted(
            ultimos_comentarios.values(), key=lambda c: c.publicado_em
        )

        dicionario_colunas: dict[str, list[object]] = {
            "id_comentario": [c.id_comentario for c in comentarios_ordenados],
            "id_video": [c.id_video for c in comentarios_ordenados],
            "id_canal": [c.id_canal for c in comentarios_ordenados],
            "id_comentario_pai": [c.id_comentario_pai or "" for c in comentarios_ordenados],
            "etag": [c.etag for c in comentarios_ordenados],
            "texto_original": [c.texto_original for c in comentarios_ordenados],
            "hash_conteudo": [c.hash_conteudo for c in comentarios_ordenados],
            "publicado_em": [c.publicado_em.isoformat() for c in comentarios_ordenados],
            "atualizado_em": [c.atualizado_em.isoformat() for c in comentarios_ordenados],
            "contagem_curtidas": [c.contagem_curtidas for c in comentarios_ordenados],
            "origem": [c.origem for c in comentarios_ordenados],
            "coletado_em": [c.coletado_em.isoformat() for c in comentarios_ordenados],
        }

        tabela = pa.Table.from_pydict(dicionario_colunas)
        buffer = io.BytesIO()
        pq.write_table(tabela, buffer)
        conteudo_parquet = buffer.getvalue()

        stamp = timestamp_versao or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        chave = self._padrao_chave.format(
            prefixo=self._prefixo,
            id_canal=id_canal,
            id_video=id_video,
            timestamp_versao=stamp,
        )

        inicio = time.perf_counter()
        self._s3.enviar_bytes(
            bucket=self._bucket,
            chave=chave,
            conteudo=conteudo_parquet,
            tipo_conteudo="application/vnd.apache.parquet",
        )
        duracao = time.perf_counter() - inicio
        MedidorDatalake.registrar_gravacao(
            camada="prata",
            formato="parquet",
            quantidade_bytes=len(conteudo_parquet),
            quantidade_registros=len(comentarios_ordenados),
            duracao_segundos=duracao,
        )
        return chave

    def carregar_snapshot_comentarios(self, chave: str) -> list[ComentarioColetado]:
        """Lê o arquivo Parquet do S3 e reconstrói as entidades ComentarioColetado."""
        inicio = time.perf_counter()
        conteudo_parquet = self._s3.baixar_bytes(bucket=self._bucket, chave=chave)
        duracao = time.perf_counter() - inicio
        MedidorDatalake.registrar_leitura(
            camada="prata",
            quantidade_bytes=len(conteudo_parquet),
            duracao_segundos=duracao,
        )
        buffer = io.BytesIO(conteudo_parquet)
        tabela = pq.read_table(buffer)
        dados = tabela.to_pydict()

        ids_comentario = cast(list[str], dados.get("id_comentario", []))
        ids_video = cast(list[str], dados.get("id_video", []))
        ids_canal = cast(list[str], dados.get("id_canal", []))
        ids_pai = cast(list[str], dados.get("id_comentario_pai", []))
        etags = cast(list[str], dados.get("etag", []))
        textos = cast(list[str], dados.get("texto_original", []))
        hashes = cast(list[str], dados.get("hash_conteudo", []))
        publicados = cast(list[str], dados.get("publicado_em", []))
        atualizados = cast(list[str], dados.get("atualizado_em", []))
        curtidas = cast(list[int], dados.get("contagem_curtidas", []))
        origens = cast(list[str], dados.get("origem", []))
        coletados = cast(list[str], dados.get("coletado_em", []))

        total = len(ids_comentario)
        comentarios: list[ComentarioColetado] = []
        for i in range(total):
            id_pai_val = ids_pai[i] if ids_pai[i] != "" else None
            comentarios.append(
                ComentarioColetado(
                    id_comentario=ids_comentario[i],
                    id_video=ids_video[i],
                    id_canal=ids_canal[i],
                    id_comentario_pai=id_pai_val,
                    etag=etags[i],
                    texto_original=textos[i],
                    hash_conteudo=hashes[i],
                    publicado_em=datetime.fromisoformat(publicados[i]),
                    atualizado_em=datetime.fromisoformat(atualizados[i]),
                    contagem_curtidas=int(curtidas[i]),
                    origem=origens[i],
                    coletado_em=datetime.fromisoformat(coletados[i]),
                )
            )

        return comentarios
