"""Métricas e instrumentação Prometheus com baixa cardinalidade para o pipeline de dados."""

from typing import final

from prometheus_client import Counter, Histogram


@final
class RegistroTelemetria:
    """Centraliza métricas operacionais sem expor identificadores pessoais ou alta cardinalidade."""

    def __init__(self) -> None:
        self.paginas_consumidas = Counter(
            "steam_pages_consumed_total",
            "Total de páginas de reviews consumidas da API Steam",
            ["appid", "status"],
        )
        self.lotes_comitados = Counter(
            "staging_batches_committed_total",
            "Total de lotes transacionais gravados no staging",
            ["appid", "tecnologia"],
        )
        self.duracao_lote_segundos = Histogram(
            "staging_batch_duration_seconds",
            "Duração em segundos para escrita e commit de lote no staging",
            ["appid"],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
        )
        self.eventos_publicados = Counter(
            "outbox_events_published_total",
            "Total de eventos da outbox confirmados no Data Lake",
            ["tipo_evento"],
        )

    def registrar_pagina(self, appid: int, sucesso: bool) -> None:
        """Incrementa contador de páginas."""
        status = "sucesso" if sucesso else "falha"
        self.paginas_consumidas.labels(appid=str(appid), status=status).inc()

    def registrar_lote(self, appid: int, tecnologia: str, duracao: float) -> None:
        """Registra a conclusão e o tempo do lote transacional."""
        self.lotes_comitados.labels(appid=str(appid), tecnologia=tecnologia).inc()
        self.duracao_lote_segundos.labels(appid=str(appid)).observe(duracao)

    def registrar_publicacao(self, tipo_evento: str) -> None:
        """Registra o sucesso de envio do evento para o Lakehouse."""
        self.eventos_publicados.labels(tipo_evento=tipo_evento).inc()
