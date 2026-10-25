"""Testes automatizados para a telemetria analítica Prometheus."""

from prometheus_client import CollectorRegistry

from app.avaliacao_modelos.metricas_estatisticas import ResultadoAvaliacao
from app.observabilidade_metricas.telemetria_analitica import TelemetriaAnalitica


def teste_telemetria_analitica_clusters() -> None:
    """Valida o registro de métricas de clustering nos Gauges Prometheus."""
    registry = CollectorRegistry()
    telemetria = TelemetriaAnalitica(registry=registry)

    avaliacao = ResultadoAvaliacao(
        total_amostras=1000,
        total_clusters=4,
        total_ruido=50,
        proporcao_ruido=0.05,
        silhouette_global=0.48,
        silhouette_sem_ruido=0.52,
        davies_bouldin=0.75,
        calinski_harabasz=210.0,
        tamanhos_clusters={0: 400, 1: 300, 2: 150, 3: 100, -1: 50},
    )

    telemetria.registrar_metricas_cluster(
        appid=427520, algoritmo="kmeans", avaliacao=avaliacao
    )

    val_clusters = registry.get_sample_value(
        "steam_clusters_total", {"appid": "427520", "algoritmo": "kmeans"}
    )
    assert val_clusters == 4.0

    val_ruido = registry.get_sample_value(
        "steam_clusters_ruido_proporcao", {"appid": "427520", "algoritmo": "kmeans"}
    )
    assert val_ruido == 0.05

    val_silhueta = registry.get_sample_value(
        "steam_clusters_silhouette_score", {"appid": "427520", "algoritmo": "kmeans"}
    )
    assert val_silhueta == 0.52

    val_db = registry.get_sample_value(
        "steam_clusters_davies_bouldin", {"appid": "427520", "algoritmo": "kmeans"}
    )
    assert val_db == 0.75

    val_ch = registry.get_sample_value(
        "steam_clusters_calinski_harabasz", {"appid": "427520", "algoritmo": "kmeans"}
    )
    assert val_ch == 210.0


def teste_telemetria_analitica_gravacao_gold() -> None:
    """Valida o incremento de contadores de artefatos comitados na camada Gold."""
    registry = CollectorRegistry()
    telemetria = TelemetriaAnalitica(registry=registry)

    telemetria.registrar_gravacao_gold(appid=427520, tipo_artefato="clusters_parquet")
    telemetria.registrar_gravacao_gold(appid=427520, tipo_artefato="clusters_parquet")
    telemetria.registrar_gravacao_gold(appid=427520, tipo_artefato="manifesto_json")

    val_parquet = registry.get_sample_value(
        "steam_gold_gravacoes_total",
        {"appid": "427520", "tipo_artefato": "clusters_parquet"},
    )
    assert val_parquet == 2.0

    val_manifesto = registry.get_sample_value(
        "steam_gold_gravacoes_total",
        {"appid": "427520", "tipo_artefato": "manifesto_json"},
    )
    assert val_manifesto == 1.0
