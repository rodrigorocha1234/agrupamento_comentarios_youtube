"""Testes de contrato e integração fim-a-fim do ciclo diário do pipeline."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from app.analise_tendencias.agregador_visoes import AgregadorVisoes
from app.analise_tendencias.calculador_tendencias import CalculadorTendencias
from app.coleta_youtube.extrator_comentarios import ExtratorComentarios
from app.coleta_youtube.modelos_coleta import ComentarioColetado, MetadadosVideo
from app.configuracao_geral.provedor_configuracao import ProvedorConfiguracao
from app.gestao_dados.camada_bronze import CamadaBronze
from app.gestao_dados.camada_ouro import CamadaOuro
from app.gestao_dados.camada_prata import CamadaPrata
from app.gestao_dados.cliente_s3 import ClienteS3
from app.orquestracao_pipeline.executor_ciclo import ExecutorCiclo
from app.orquestracao_pipeline.protocolos_ciclo import (
    ProtocoloExecutorCiclo,
)
from app.servico_api.esquemas_respostas import (
    RespostaClustersVideo,
    RespostaTendenciasCanal,
    RespostaTendenciasVideo,
)
from app.tratamento_texto.lematizador_spacy import LematizadorSpacy
from app.tratamento_texto.rotulador_topicos import RotuladorTopicos


def test_contrato_esquemas_api() -> None:
    """Verifica se os modelos Pydantic validam campos obrigatórios conforme as especificações."""
    dados_canal = {
        "id_canal": "UC_CONTRATO",
        "tecnica": "kmeans",
        "janela": "7dias",
        "topicos": [
            {
                "topico": "dados",
                "contagem_atual": 15,
                "contagem_anterior": 10,
                "variacao_proporcao": 0.5,
                "status_tendencia": "crescendo",
                "comentarios": ["C1", "C2"],
            }
        ],
    }
    modelo_canal = RespostaTendenciasCanal.model_validate(dados_canal)
    assert modelo_canal.id_canal == "UC_CONTRATO"
    assert modelo_canal.topicos[0].topico == "dados"
    assert modelo_canal.topicos[0].comentarios == ["C1", "C2"]

    dados_video = {
        "id_canal": "UC_CONTRATO",
        "id_video": "VID_1",
        "tecnica": "dbscan",
        "janela": "7dias",
        "topicos": [],
    }
    modelo_video = RespostaTendenciasVideo.model_validate(dados_video)
    assert modelo_video.id_video == "VID_1"

    dados_clusters = {
        "id_canal": "UC_CONTRATO",
        "id_video": "VID_1",
        "tecnica": "kmeans",
        "quantidade_clusters": 2,
        "fracao_ruido": 0.0,
        "clusters": [
            {
                "cluster_id": 0,
                "rotulo_topico": "ia",
                "total_comentarios": 10,
                "percentual_total": 50.0,
            }
        ],
    }
    modelo_clusters = RespostaClustersVideo.model_validate(dados_clusters)
    assert modelo_clusters.quantidade_clusters == 2


def test_fluxo_completo_executor_ciclo() -> None:
    """Simula o ciclo diário ponta a ponta integrando todos os subsistemas em memória."""
    caminho_yaml = Path(__file__).resolve().parent.parent / "config" / "entradas.yaml"
    config = ProvedorConfiguracao(caminho_yaml).carregar()

    # Mocks em memória para dependências externas de I/O
    s3_cliente = MagicMock(spec=ClienteS3)
    bucket = "youtube-comentarios"
    bronze = CamadaBronze(s3_cliente, bucket=bucket)
    prata = CamadaPrata(s3_cliente, bucket=bucket)
    ouro = CamadaOuro(s3_cliente, bucket=bucket)

    agora = datetime.now(timezone.utc)
    video_mock = MetadadosVideo(
        id_video="VID_FLUXO",
        id_canal="UC_FLUXO",
        titulo="Vídeo de Teste Completo",
        publicado_em=agora,
    )
    comentarios_sinteticos: list[ComentarioColetado] = [
        ComentarioColetado(
            id_comentario=f"COMM_{i}",
            id_video="VID_FLUXO",
            id_canal="UC_FLUXO",
            id_comentario_pai=None,
            etag=f"etag_{i}",
            texto_original=f"Excelente conteúdo sobre inteligência artificial e aprendizado de máquina número {i}",
            hash_conteudo=f"hash_{i}",
            publicado_em=agora,
            atualizado_em=agora,
            contagem_curtidas=i,
            origem="principal",
            coletado_em=agora,
        )
        for i in range(12)
    ]

    extrator_mock = MagicMock(spec=ExtratorComentarios)
    extrator_mock.extrair_canal_completo.return_value = ([video_mock], comentarios_sinteticos)

    lematizador = LematizadorSpacy(
        modelo_nome="pt_core_news_sm",
        preservar_negacoes=["nao", "não", "nunca", "sem"],
    )
    rotulador = RotuladorTopicos()
    calculador = CalculadorTendencias(janela_dias=7)
    agregador = AgregadorVisoes()

    executor = ExecutorCiclo(
        config=config,
        extrator=extrator_mock,
        bronze=bronze,
        prata=prata,
        ouro=ouro,
        lematizador=lematizador,
        rotulador=rotulador,
        calculador_tendencias=calculador,
        agregador_visoes=agregador,
        rastreador_mlflow=None,
    )

    resultado = executor.executar_ciclo_canal("UC_FLUXO")

    assert isinstance(executor, ProtocoloExecutorCiclo)
    assert resultado["videos"] == 1
    assert resultado["comentarios"] == 12
    assert resultado["topicos_ouro"] > 0
    # Verifica que chamadas S3 ocorreram sem salvar arquivos locais
    assert s3_cliente.enviar_bytes.called


def test_protocolo_executor_ciclo_e_inversao_dependencias() -> None:
    """Valida a conformidade estrutural com ProtocoloExecutorCiclo e flexibilidade para mocks."""
    class ExecutorCustomizado:
        """Dublê customizado satisfazendo ProtocoloExecutorCiclo."""

        def executar_ciclo_canal(self, id_canal: str) -> dict[str, int]:
            return {"videos": 5, "comentarios": 100, "topicos_ouro": 10}

    instancia_customizada = ExecutorCustomizado()
    assert isinstance(instancia_customizada, ProtocoloExecutorCiclo)
    res = instancia_customizada.executar_ciclo_canal("UC_TESTE")
    assert res["videos"] == 5

