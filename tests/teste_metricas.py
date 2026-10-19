"""Testes unitários e de integração para telemetria e observabilidade com Prometheus."""

from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.coleta_metricas.medidor_coleta import (
    MedidorColeta,
)
from app.coleta_metricas.medidor_datalake import (
    MedidorDatalake,
)
from app.coleta_metricas.medidor_modelos import (
    MedidorModelos,
)
from app.servico_api.aplicacao_fastapi import criar_aplicacao


def test_medidor_coleta_incrementa_contadores() -> None:
    """Valida registro e incremento de comentários e erros no coletor via REGISTRY público."""
    valor_inicial = REGISTRY.get_sample_value(
        "youtube_coleta_comentarios_total", {"status": "sucesso", "origem": "principal"}
    ) or 0.0

    MedidorColeta.registrar_comentarios_coletados(15, origem="principal")

    valor_final = REGISTRY.get_sample_value(
        "youtube_coleta_comentarios_total", {"status": "sucesso", "origem": "principal"}
    ) or 0.0
    assert valor_final == valor_inicial + 15.0

    erros_inicial = REGISTRY.get_sample_value(
        "youtube_coleta_erros_total", {"tipo_erro": "quota"}
    ) or 0.0

    MedidorColeta.registrar_erro("quota")

    erros_final = REGISTRY.get_sample_value(
        "youtube_coleta_erros_total", {"tipo_erro": "quota"}
    ) or 0.0
    assert erros_final == erros_inicial + 1.0

    # Valida registro de tempo de execução individual do pipeline
    MedidorColeta.registrar_execucao_pipeline(duracao_segundos=18.5, canal="UC_TESTE", sucesso=True)
    gauge_val = REGISTRY.get_sample_value(
        "youtube_pipeline_ultima_execucao_duracao_segundos", {"canal": "UC_TESTE"}
    )
    assert gauge_val == 18.5


def test_medidor_modelos_atualiza_gauges() -> None:
    """Valida gauges de qualidade de modelo e proporção de ruído via REGISTRY público."""
    MedidorModelos.atualizar_metricas_cluster(
        tecnica="kmeans",
        quantidade_clusters=5,
        fracao_ruido=0.12,
        silhueta=0.68,
    )

    qtd = REGISTRY.get_sample_value("youtube_cluster_quantidade", {"tecnica": "kmeans"})
    ruido = REGISTRY.get_sample_value("youtube_cluster_ruido_razao", {"tecnica": "kmeans"})
    silh = REGISTRY.get_sample_value("youtube_cluster_silhueta_score", {"tecnica": "kmeans"})

    assert qtd == 5.0
    assert ruido == 0.12
    assert silh == 0.68


def test_endpoint_metrics_e_middleware_latencia() -> None:
    """Valida geração do endpoint /metrics e telemetria HTTP."""
    app = criar_aplicacao()
    cliente = TestClient(app)

    # Dispara uma requisição HTTP para gerar métricas de rota
    resp_health = cliente.get("/health")
    assert resp_health.status_code == 200

    resp_metrics = cliente.get("/metrics")
    assert resp_metrics.status_code == 200
    texto_metrics = resp_metrics.text
    assert "youtube_api_requisicoes_total" in texto_metrics
    assert "youtube_api_latencia_segundos" in texto_metrics


def test_medidor_datalake_telemetria_s3() -> None:
    """Valida gravação, leitura e erros do Data Lakehouse no REGISTRY público do Prometheus."""
    bytes_ini = REGISTRY.get_sample_value(
        "youtube_datalake_bytes_total", {"camada": "bronze", "operacao": "gravacao"}
    ) or 0.0
    arq_ini = REGISTRY.get_sample_value(
        "youtube_datalake_arquivos_total", {"camada": "bronze", "formato": "jsonl"}
    ) or 0.0
    reg_ini = REGISTRY.get_sample_value(
        "youtube_datalake_registros_total", {"camada": "bronze"}
    ) or 0.0

    MedidorDatalake.registrar_gravacao("bronze", "jsonl", 4096, 50, 0.02)

    bytes_fim = REGISTRY.get_sample_value(
        "youtube_datalake_bytes_total", {"camada": "bronze", "operacao": "gravacao"}
    ) or 0.0
    arq_fim = REGISTRY.get_sample_value(
        "youtube_datalake_arquivos_total", {"camada": "bronze", "formato": "jsonl"}
    ) or 0.0
    reg_fim = REGISTRY.get_sample_value(
        "youtube_datalake_registros_total", {"camada": "bronze"}
    ) or 0.0

    assert bytes_fim == bytes_ini + 4096.0
    assert arq_fim == arq_ini + 1.0
    assert reg_fim == reg_ini + 50.0

    # Leitura prata
    leitura_ini = REGISTRY.get_sample_value(
        "youtube_datalake_bytes_total", {"camada": "prata", "operacao": "leitura"}
    ) or 0.0
    MedidorDatalake.registrar_leitura("prata", 8192, 0.01)
    leitura_fim = REGISTRY.get_sample_value(
        "youtube_datalake_bytes_total", {"camada": "prata", "operacao": "leitura"}
    ) or 0.0
    assert leitura_fim == leitura_ini + 8192.0

    # Erro ouro
    erro_ini = REGISTRY.get_sample_value(
        "youtube_datalake_erros_total", {"camada": "ouro", "tipo_erro": "timeout"}
    ) or 0.0
    MedidorDatalake.registrar_erro("ouro", "timeout")
    erro_fim = REGISTRY.get_sample_value(
        "youtube_datalake_erros_total", {"camada": "ouro", "tipo_erro": "timeout"}
    ) or 0.0
    assert erro_fim == erro_ini + 1.0
