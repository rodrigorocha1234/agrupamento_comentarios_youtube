"""Instrumentação de métricas operacionais e de qualidade de modelos com Prometheus."""

from prometheus_client import Gauge

MEDIDOR_RUIDO_RAZAO = Gauge(
    "youtube_cluster_ruido_razao",
    "Fração de ruído (outliers label -1) identificado por técnica de clusterização",
    ["tecnica"],
)

MEDIDOR_CLUSTERS_QUANTIDADE = Gauge(
    "youtube_cluster_quantidade",
    "Número efetivo de clusters encontrados por técnica",
    ["tecnica"],
)

MEDIDOR_SILHUETA_SCORE = Gauge(
    "youtube_cluster_silhueta_score",
    "Pontuação de silhueta média do agrupamento por técnica",
    ["tecnica"],
)


class MedidorModelos:
    """Registra métricas analíticas e de qualidade dos modelos no Prometheus."""

    @staticmethod
    def atualizar_metricas_cluster(
        tecnica: str,
        quantidade_clusters: int,
        fracao_ruido: float,
        silhueta: float | None = None,
    ) -> None:
        """Atualiza os gauges do Prometheus para a técnica informada."""
        MEDIDOR_RUIDO_RAZAO.labels(tecnica=tecnica).set(fracao_ruido)
        MEDIDOR_CLUSTERS_QUANTIDADE.labels(tecnica=tecnica).set(quantidade_clusters)
        if silhueta is not None:
            MEDIDOR_SILHUETA_SCORE.labels(tecnica=tecnica).set(silhueta)
