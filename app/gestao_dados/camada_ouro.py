"""Gestão da camada Ouro (agregações de tópicos, clusters e tendências em Parquet)."""

from dataclasses import dataclass
from datetime import datetime, timezone
import io
import time
from typing import cast
import pyarrow as pa
import pyarrow.parquet as pq

from app.coleta_metricas.medidor_datalake import MedidorDatalake
from app.configuracao_geral.tipos_enumerados import (
    CamadaLakehouse,
    JanelaTemporal,
    StatusTendencia,
    TecnicaCluster,
)
from app.gestao_dados.cliente_s3 import ClienteS3


@dataclass(frozen=True, slots=True)
class RegistroTopicoOuro:
    """Representação de um tópico calculado persistido na camada Ouro."""

    id_canal: str
    id_video: str
    tecnica: TecnicaCluster | str
    topico: str
    contagem_atual: int
    contagem_anterior: int
    variacao_proporcao: float
    status_tendencia: StatusTendencia | str
    comentarios_amostra: str
    janela: JanelaTemporal | str = ""
    data_referencia: str = ""
    percentual_variacao: float = 0.0


class CamadaOuro:
    """Gerencia a persistência e consulta analítica da camada Ouro no S3."""

    def __init__(
        self,
        cliente_s3: ClienteS3,
        bucket: str,
        prefixo_ouro: CamadaLakehouse | str = CamadaLakehouse.OURO,
        padrao_chave_video: str | None = None,
        padrao_chave_consolidado: str | None = None,
    ) -> None:
        self._s3: ClienteS3 = cliente_s3
        self._bucket: str = bucket
        self._prefixo: str = str(prefixo_ouro)
        self._padrao_chave_video: str = padrao_chave_video or (
            "{prefixo}/id_canal={id_canal}/id_video={id_video}/"
            "tecnica={tecnica}/data={data_referencia}/topicos.parquet"
        )
        self._padrao_chave_consolidado: str = padrao_chave_consolidado or (
            "{prefixo}/id_canal={id_canal}/consolidado/"
            "tecnica={tecnica}/data={data_referencia}/topicos.parquet"
        )

    def gravar_topicos_video(
        self,
        id_canal: str,
        id_video: str,
        tecnica: str,
        topicos: list[RegistroTopicoOuro],
        janela: str = "",
        data_referencia: str | None = None,
    ) -> str:
        """Persiste os tópicos de um vídeo específico na camada Ouro particionados por data."""
        data_ref = (
            data_referencia
            or (topicos[0].data_referencia if topicos and topicos[0].data_referencia else "")
            or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        )
        kwargs = {
            "prefixo": self._prefixo,
            "id_canal": id_canal,
            "id_video": id_video,
            "tecnica": tecnica,
            "janela": janela,
            "data_referencia": data_ref,
            "data": data_ref,
        }
        chave = self._padrao_chave_video.format(**kwargs)
        self._salvar_tabela_topicos(chave, topicos)
        return chave

    def gravar_topicos_canal_consolidado(
        self,
        id_canal: str,
        tecnica: str,
        topicos: list[RegistroTopicoOuro],
        janela: str = "",
        data_referencia: str | None = None,
    ) -> str:
        """Persiste a visão consolidada de tópicos do canal na camada Ouro particionada por data."""
        data_ref = (
            data_referencia
            or (topicos[0].data_referencia if topicos and topicos[0].data_referencia else "")
            or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        )
        kwargs = {
            "prefixo": self._prefixo,
            "id_canal": id_canal,
            "tecnica": tecnica,
            "janela": janela,
            "data_referencia": data_ref,
            "data": data_ref,
        }
        chave = self._padrao_chave_consolidado.format(**kwargs)
        self._salvar_tabela_topicos(chave, topicos)
        return chave

    def carregar_topicos(self, chave: str) -> list[RegistroTopicoOuro]:
        """Carrega e desserializa os tópicos de uma partição da camada Ouro."""
        inicio = time.perf_counter()
        conteudo = self._s3.baixar_bytes(bucket=self._bucket, chave=chave)
        duracao = time.perf_counter() - inicio
        MedidorDatalake.registrar_leitura("ouro", len(conteudo), duracao)

        buffer = io.BytesIO(conteudo)
        tabela = pq.read_table(buffer)
        dados = tabela.to_pydict()

        canais = cast(list[str], dados.get("id_canal", []))
        videos = cast(list[str], dados.get("id_video", []))
        tecnicas = cast(list[str], dados.get("tecnica", []))
        topicos_nomes = cast(list[str], dados.get("topico", []))
        atuais = cast(list[int], dados.get("contagem_atual", []))
        anteriores = cast(list[int], dados.get("contagem_anterior", []))
        variacoes = cast(list[float], dados.get("variacao_proporcao", []))
        status_lista = cast(list[str], dados.get("status_tendencia", []))
        amostras = cast(list[str], dados.get("comentarios_amostra", []))
        janelas = cast(list[str], dados.get("janela", []))
        datas = cast(list[str], dados.get("data_referencia", []))
        percentuais = cast(list[float], dados.get("percentual_variacao", []))

        total = len(canais)
        resultado: list[RegistroTopicoOuro] = []
        for i in range(total):
            data_item = datas[i] if i < len(datas) else ""
            perc_item = (
                percentuais[i]
                if i < len(percentuais)
                else round(float(variacoes[i]) * 100.0, 2)
            )
            resultado.append(
                RegistroTopicoOuro(
                    id_canal=canais[i],
                    id_video=videos[i],
                    tecnica=tecnicas[i],
                    topico=topicos_nomes[i],
                    contagem_atual=int(atuais[i]),
                    contagem_anterior=int(anteriores[i]),
                    variacao_proporcao=float(variacoes[i]),
                    status_tendencia=status_lista[i],
                    comentarios_amostra=amostras[i],
                    janela=janelas[i],
                    data_referencia=str(data_item),
                    percentual_variacao=float(perc_item),
                )
            )
        return resultado

    def _salvar_tabela_topicos(self, chave: str, topicos: list[RegistroTopicoOuro]) -> None:
        """Converte registros para tabela Parquet e envia ao S3 via BytesIO."""
        dicionario_colunas: dict[str, list[object]] = {
            "id_canal": [t.id_canal for t in topicos],
            "id_video": [t.id_video for t in topicos],
            "tecnica": [t.tecnica for t in topicos],
            "topico": [t.topico for t in topicos],
            "contagem_atual": [t.contagem_atual for t in topicos],
            "contagem_anterior": [t.contagem_anterior for t in topicos],
            "variacao_proporcao": [t.variacao_proporcao for t in topicos],
            "status_tendencia": [t.status_tendencia for t in topicos],
            "comentarios_amostra": [t.comentarios_amostra for t in topicos],
            "janela": [t.janela for t in topicos],
            "data_referencia": [t.data_referencia for t in topicos],
            "percentual_variacao": [t.percentual_variacao for t in topicos],
        }
        tabela = pa.Table.from_pydict(dicionario_colunas)
        buffer = io.BytesIO()
        pq.write_table(tabela, buffer)
        conteudo_parquet = buffer.getvalue()

        inicio = time.perf_counter()
        self._s3.enviar_bytes(
            bucket=self._bucket,
            chave=chave,
            conteudo=conteudo_parquet,
            tipo_conteudo="application/vnd.apache.parquet",
        )
        duracao = time.perf_counter() - inicio
        MedidorDatalake.registrar_gravacao(
            camada="ouro",
            formato="parquet",
            quantidade_bytes=len(conteudo_parquet),
            quantidade_registros=len(topicos),
            duracao_segundos=duracao,
        )

    def gravar_catalogo_videos(
        self,
        id_canal: str,
        nome_canal: str,
        videos: list[tuple[str, str]],
    ) -> str:
        """Persiste os metadados dos vídeos do canal na camada Ouro em Parquet."""
        chave = f"{self._prefixo}/id_canal={id_canal}/catalogo_videos.parquet"
        dicionario_colunas: dict[str, list[object]] = {
            "id_canal": [id_canal for _ in videos],
            "nome_canal": [nome_canal for _ in videos],
            "id_video": [v[0] for v in videos],
            "nome_video": [v[1] for v in videos],
        }
        tabela = pa.Table.from_pydict(dicionario_colunas)
        buffer = io.BytesIO()
        pq.write_table(tabela, buffer)
        conteudo_parquet = buffer.getvalue()

        self._s3.enviar_bytes(
            bucket=self._bucket,
            chave=chave,
            conteudo=conteudo_parquet,
            tipo_conteudo="application/vnd.apache.parquet",
        )
        return chave

    def carregar_catalogo_videos(self, id_canal: str) -> tuple[str, list[tuple[str, str]]]:
        """Recupera o nome do canal e a lista de (id_video, nome_video) gravada no S3."""
        chave = f"{self._prefixo}/id_canal={id_canal}/catalogo_videos.parquet"
        conteudo = self._s3.baixar_bytes(bucket=self._bucket, chave=chave)
        buffer = io.BytesIO(conteudo)
        tabela = pq.read_table(buffer)
        dados = tabela.to_pydict()
        nomes_canal = cast(list[str], dados.get("nome_canal", []))
        ids_videos = cast(list[str], dados.get("id_video", []))
        nomes_videos = cast(list[str], dados.get("nome_video", []))
        nome_canal = nomes_canal[0] if nomes_canal else id_canal
        pares = [(ids_videos[i], nomes_videos[i]) for i in range(len(ids_videos))]
        return nome_canal, pares

    def listar_videos_conhecidos(self, id_canal: str) -> list[str]:
        """Descobre os IDs de vídeos processados no S3 a partir das partições existentes."""
        prefixo = f"{self._prefixo}/id_canal={id_canal}/id_video="
        chaves = self._s3.listar_chaves(bucket=self._bucket, prefixo=prefixo)
        ids_encontrados: set[str] = set()
        for c in chaves:
            # Ex: ouro/id_canal=.../id_video=XYZ/tecnica=...
            partes = c.split("/")
            for p in partes:
                if p.startswith("id_video="):
                    vid = p.split("=", 1)[1]
                    if vid:
                        ids_encontrados.add(vid)
        return sorted(ids_encontrados)

    def listar_datas_tendencias(
        self,
        id_canal: str,
        tecnica: str,
        consolidado: bool = True,
        id_video: str | None = None,
    ) -> list[str]:
        """Descobre as datas em que foram geradas trends no S3."""
        if consolidado or not id_video:
            prefixo = f"{self._prefixo}/id_canal={id_canal}/consolidado/tecnica={tecnica}/"
        else:
            prefixo = f"{self._prefixo}/id_canal={id_canal}/id_video={id_video}/tecnica={tecnica}/"

        chaves = self._s3.listar_chaves(bucket=self._bucket, prefixo=prefixo)
        datas: set[str] = set()
        for c in chaves:
            for parte in c.split("/"):
                if parte.startswith("data=") or parte.startswith("data_coleta=") or parte.startswith("data_referencia="):
                    val = parte.split("=", 1)[1]
                    if val:
                        datas.add(val)
        return sorted(datas, reverse=True)

    def obter_chave_tendencias(
        self,
        id_canal: str,
        tecnica: str,
        data: str | None = None,
        consolidado: bool = True,
        id_video: str | None = None,
        janela: str = "",
    ) -> str:
        """Determina a chave S3 correspondente para a data solicitada ou mais recente."""
        datas = self.listar_datas_tendencias(id_canal, tecnica, consolidado=consolidado, id_video=id_video)
        data_efetiva = data or (datas[0] if datas else datetime.now(timezone.utc).strftime("%Y-%m-%d"))

        if consolidado or not id_video:
            return self._padrao_chave_consolidado.format(
                prefixo=self._prefixo,
                id_canal=id_canal,
                tecnica=tecnica,
                janela=janela,
                data_referencia=data_efetiva,
                data=data_efetiva,
            )
        return self._padrao_chave_video.format(
            prefixo=self._prefixo,
            id_canal=id_canal,
            id_video=id_video,
            tecnica=tecnica,
            janela=janela,
            data_referencia=data_efetiva,
            data=data_efetiva,
        )
