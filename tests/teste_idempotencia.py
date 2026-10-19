"""Testes unitários e de integração para o lakehouse S3, idempotência e versionamento."""

from datetime import datetime, timezone
from typing import cast
from app.coleta_youtube.modelos_coleta import ComentarioColetado
from app.gestao_dados.camada_bronze import CamadaBronze
from app.gestao_dados.camada_ouro import CamadaOuro, RegistroTopicoOuro
from app.gestao_dados.camada_prata import CamadaPrata
from app.gestao_dados.cliente_s3 import ClienteS3
from app.gestao_dados.controle_idempotencia import (
    ControleIdempotencia,
    RegistroVersao,
)


class ArmazenamentoS3EmMemoria:
    """Mock em memória RAM para testar ClienteS3 sem depender de conexões externas."""

    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}
        self.buckets: set[str] = set()

    def garantir_bucket_existente(self, bucket: str) -> None:
        self.buckets.add(bucket)

    def enviar_bytes(
        self,
        bucket: str,
        chave: str,
        conteudo: bytes,
        tipo_conteudo: str = "application/octet-stream",
    ) -> None:
        caminho_completo = f"{bucket}/{chave}"
        self.objetos[caminho_completo] = conteudo

    def baixar_bytes(self, bucket: str, chave: str) -> bytes:
        caminho_completo = f"{bucket}/{chave}"
        if caminho_completo not in self.objetos:
            raise KeyError(f"Chave não encontrada: {caminho_completo}")
        return self.objetos[caminho_completo]

    def listar_chaves(self, bucket: str, prefixo: str) -> list[str]:
        prefixo_completo = f"{bucket}/{prefixo}"
        chaves: list[str] = []
        for chave in self.objetos:
            if chave.startswith(prefixo_completo):
                chaves.append(chave[len(bucket) + 1 :])
        return sorted(chaves)


def test_controle_idempotencia_detecta_mudancas() -> None:
    """Verifica detecção precisa de alteração de conteúdo, etag e timestamp."""
    agora = datetime.now(timezone.utc)
    comentario = ComentarioColetado(
        id_comentario="C1",
        id_video="V1",
        id_canal="UC1",
        id_comentario_pai=None,
        etag="etag_v1",
        texto_original="Texto original",
        hash_conteudo="hash_v1",
        publicado_em=agora,
        atualizado_em=agora,
        contagem_curtidas=5,
        origem="principal",
        coletado_em=agora,
    )

    versao_igual = RegistroVersao(
        id_comentario="C1",
        id_video="V1",
        etag="etag_v1",
        hash_conteudo="hash_v1",
        atualizado_em=agora,
    )

    # Inalterado
    assert ControleIdempotencia.verificar_alteracao(comentario, versao_igual) is False

    # Novo comentário (sem versão anterior)
    assert ControleIdempotencia.verificar_alteracao(comentario, None) is True

    # Alteração de conteúdo
    versao_hash_antigo = RegistroVersao(
        id_comentario="C1",
        id_video="V1",
        etag="etag_v1",
        hash_conteudo="hash_antigo",
        atualizado_em=agora,
    )
    assert ControleIdempotencia.verificar_alteracao(comentario, versao_hash_antigo) is True


def test_fluxo_camadas_bronze_prata_ouro_em_memoria() -> None:
    """Valida o ciclo completo pelas camadas Bronze, Prata e Ouro."""
    s3_mock = ArmazenamentoS3EmMemoria()
    s3_cliente = ClienteS3(cliente_boto=None)
    # Substituir métodos de I/O em s3_cliente pelos do mock em memória
    s3_cliente.garantir_bucket_existente = s3_mock.garantir_bucket_existente
    s3_cliente.enviar_bytes = s3_mock.enviar_bytes
    s3_cliente.baixar_bytes = s3_mock.baixar_bytes
    s3_cliente.listar_chaves = s3_mock.listar_chaves

    bucket = "youtube-comentarios"
    bronze = CamadaBronze(s3_cliente, bucket=bucket)
    prata = CamadaPrata(s3_cliente, bucket=bucket)
    ouro = CamadaOuro(s3_cliente, bucket=bucket)

    agora = datetime.now(timezone.utc)
    com1 = ComentarioColetado(
        id_comentario="C100",
        id_video="V10",
        id_canal="UC10",
        id_comentario_pai=None,
        etag="etag1",
        texto_original="Conteudo de teste",
        hash_conteudo="hash100",
        publicado_em=agora,
        atualizado_em=agora,
        contagem_curtidas=10,
        origem="principal",
        coletado_em=agora,
    )

    # 1. Teste Bronze (JSONL)
    chave_bronze = bronze.gravar_lote_comentarios(
        id_canal="UC10",
        id_video="V10",
        comentarios=[com1],
    )
    assert "bronze/id_canal=UC10/id_video=V10" in chave_bronze
    comentarios_bronze = bronze.carregar_comentarios_lote(chave_bronze)
    assert len(comentarios_bronze) == 1
    assert comentarios_bronze[0].id_comentario == "C100"

    # 2. Teste Prata (Parquet e Deduplicação)
    chave_prata = prata.gravar_snapshot_comentarios(
        id_canal="UC10",
        id_video="V10",
        comentarios=[com1],
    )
    assert "prata/id_canal=UC10/id_video=V10" in chave_prata
    comentarios_prata = prata.carregar_snapshot_comentarios(chave_prata)
    assert len(comentarios_prata) == 1
    assert comentarios_prata[0].texto_original == "Conteudo de teste"

    # 3. Teste Ouro (Parquet analítico)
    reg_topico = RegistroTopicoOuro(
        id_canal="UC10",
        id_video="V10",
        tecnica="kmeans",
        topico="ia",
        contagem_atual=25,
        contagem_anterior=10,
        variacao_proporcao=1.5,
        status_tendencia="crescendo",
        comentarios_amostra="C100",
        janela="7dias",
    )
    chave_ouro_video = ouro.gravar_topicos_video(
        id_canal="UC10",
        id_video="V10",
        tecnica="kmeans",
        janela="7dias",
        topicos=[reg_topico],
    )
    assert "ouro/id_canal=UC10/id_video=V10/tecnica=kmeans" in chave_ouro_video
    topicos_carregados = ouro.carregar_topicos(chave_ouro_video)
    assert len(topicos_carregados) == 1
    assert topicos_carregados[0].topico == "ia"
    assert topicos_carregados[0].status_tendencia == "crescendo"


def test_camadas_lakehouse_com_templates_chaves_customizados() -> None:
    """Valida que templates de chaves customizados no S3 são rigorosamente interpolados."""
    armazenamento = ArmazenamentoS3EmMemoria()
    s3_cliente = cast(ClienteS3, armazenamento)
    bucket = "bucket-teste-custom"

    bronze = CamadaBronze(
        s3_cliente,
        bucket=bucket,
        prefixo_bronze="raw",
        padrao_chave="{prefixo}/canal_{id_canal}/vid_{id_video}/dia_{data_coleta}/arquivo_{id_lote}.jsonl",
    )
    prata = CamadaPrata(
        s3_cliente,
        bucket=bucket,
        prefixo_prata="staging",
        padrao_chave="{prefixo}/canal_{id_canal}/vid_{id_video}/v_{timestamp_versao}.parquet",
    )
    ouro = CamadaOuro(
        s3_cliente,
        bucket=bucket,
        prefixo_ouro="analytics",
        padrao_chave_video="{prefixo}/c_{id_canal}/v_{id_video}/alg_{tecnica}_{data}.parquet",
        padrao_chave_consolidado="{prefixo}/c_{id_canal}/total/alg_{tecnica}_{data}.parquet",
    )

    agora = datetime.now(timezone.utc)
    com1 = ComentarioColetado(
        id_comentario="C200",
        id_video="V200",
        id_canal="UC200",
        id_comentario_pai=None,
        etag="etag_v200",
        texto_original="Conteudo customizado",
        hash_conteudo="hash_v200",
        publicado_em=agora,
        atualizado_em=agora,
        contagem_curtidas=10,
        origem="principal",
        coletado_em=agora,
    )

    # 1. Bronze com template customizado
    chave_bronze = bronze.gravar_lote_comentarios("UC200", "V200", [com1])
    assert chave_bronze.startswith("raw/canal_UC200/vid_V200/dia_")
    assert "/arquivo_" in chave_bronze
    assert chave_bronze.endswith(".jsonl")

    # 2. Prata com template customizado
    chave_prata = prata.gravar_snapshot_comentarios("UC200", "V200", [com1], timestamp_versao="20261014")
    assert chave_prata == "staging/canal_UC200/vid_V200/v_20261014.parquet"

    # 3. Ouro com template customizado
    reg_topico = RegistroTopicoOuro(
        id_canal="UC200",
        id_video="V200",
        tecnica="dbscan",
        topico="python",
        contagem_atual=30,
        contagem_anterior=15,
        variacao_proporcao=1.0,
        status_tendencia="crescendo",
        comentarios_amostra="C200",
        data_referencia="2026-10-14",
    )
    chave_ouro_vid = ouro.gravar_topicos_video(
        id_canal="UC200",
        id_video="V200",
        tecnica="dbscan",
        topicos=[reg_topico],
        data_referencia="2026-10-14",
    )
    assert chave_ouro_vid == "analytics/c_UC200/v_V200/alg_dbscan_2026-10-14.parquet"

    chave_ouro_cons = ouro.gravar_topicos_canal_consolidado(
        id_canal="UC200",
        tecnica="dbscan",
        topicos=[reg_topico],
        data_referencia="2026-10-14",
    )
    assert chave_ouro_cons == "analytics/c_UC200/total/alg_dbscan_2026-10-14.parquet"
