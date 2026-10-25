"""Métricas analíticas e de modelagem no Prometheus com estrita baixa cardinalidade."""

from typing import final

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge

from app.avaliacao_modelos.metricas_estatisticas import ResultadoAvaliacao


@final
class TelemetriaAnalitica:
    """Instrumenta métricas de qualidade de clustering e linhagem Gold para o Prometheus."""

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        alvo_registry = registry or REGISTRY

        self.clusters_total = Gauge(
            "steam_clusters_total",
            "Total de clusters válidos identificados na partição",
            ["appid", "algoritmo"],
            registry=alvo_registry,
        )
        self.ruido_proporcao = Gauge(
            "steam_clusters_ruido_proporcao",
            "Proporção de amostras classificadas como ruído ou outliers",
            ["appid", "algoritmo"],
            registry=alvo_registry,
        )
        self.silhouette_score = Gauge(
            "steam_clusters_silhouette_score",
            "Coeficiente de silhueta médio (sem ruído quando aplicável)",
            ["appid", "algoritmo"],
            registry=alvo_registry,
        )
        self.davies_bouldin = Gauge(
            "steam_clusters_davies_bouldin",
            "Índice Davies-Bouldin de coesão e separação de clusters",
            ["appid", "algoritmo"],
            registry=alvo_registry,
        )
        self.calinski_harabasz = Gauge(
            "steam_clusters_calinski_harabasz",
            "Índice Calinski-Harabasz da partição",
            ["appid", "algoritmo"],
            registry=alvo_registry,
        )
        self.gold_gravacoes_total = Counter(
            "steam_gold_gravacoes_total",
            "Total de gravações de dados e metadados persistidos na camada Gold",
            ["appid", "tipo_artefato"],
            registry=alvo_registry,
        )

    def registrar_metricas_cluster(
        self, appid: int, algoritmo: str, avaliacao: ResultadoAvaliacao
    ) -> None:
        """Atualiza os gauges do Prometheus com as métricas estatísticas da partição."""
        str_appid = str(appid)
        self.clusters_total.labels(appid=str_appid, algoritmo=algoritmo).set(
            float(avaliacao.total_clusters)
        )
        self.ruido_proporcao.labels(appid=str_appid, algoritmo=algoritmo).set(
            float(avaliacao.proporcao_ruido)
        )

        score_silhueta = (
            avaliacao.silhouette_sem_ruido
            if avaliacao.silhouette_sem_ruido is not None
            else avaliacao.silhouette_global
        )
        if score_silhueta is not None:
            self.silhouette_score.labels(appid=str_appid, algoritmo=algoritmo).set(
                float(score_silhueta)
            )

        if avaliacao.davies_bouldin is not None:
            self.davies_bouldin.labels(appid=str_appid, algoritmo=algoritmo).set(
                float(avaliacao.davies_bouldin)
            )

        if avaliacao.calinski_harabasz is not None:
            self.calinski_harabasz.labels(appid=str_appid, algoritmo=algoritmo).set(
                float(avaliacao.calinski_harabasz)
            )

    def registrar_gravacao_gold(self, appid: int, tipo_artefato: str) -> None:
        """Incrementa contador de artefatos comitados com sucesso na camada Gold."""
        self.gold_gravacoes_total.labels(
            appid=str(appid), tipo_artefato=tipo_artefato
        ).inc()
