"""Instrumentação de métricas de coleta e ingestão com Prometheus."""

from prometheus_client import Counter, Gauge, Histogram

# Métricas com cardinalidade estritamente controlada (sem id_video nem id_comentario)
CONTADOR_COLETA_COMENTARIOS = Counter(
    "youtube_coleta_comentarios_total",
    "Total acumulado de comentários e respostas coletados da YouTube API",
    ["status", "origem"],
)

CONTADOR_COLETA_ERROS = Counter(
    "youtube_coleta_erros_total",
    "Total de erros ocorridos na comunicação com a API do YouTube",
    ["tipo_erro"],
)

HISTOGRAMA_ETAPAS_PIPELINE = Histogram(
    "youtube_pipeline_duracao_segundos",
    "Tempo de execução em segundos de cada etapa do pipeline",
    ["etapa"],
)

GAUGE_PIPELINE_ULTIMA_EXECUCAO = Gauge(
    "youtube_pipeline_ultima_execucao_duracao_segundos",
    "Duração em segundos da última execução individual do pipeline",
    ["canal"],
)

HISTOGRAMA_PIPELINE_EXECUCAO = Histogram(
    "youtube_pipeline_ciclo_duracao_segundos",
    "Duração total em segundos de cada ciclo de execução do pipeline",
    ["status"],
)


class MedidorColeta:
    """Registra eventos de telemetria da etapa de coleta e execução do pipeline."""

    @staticmethod
    def registrar_comentarios_coletados(quantidade: int, origem: str = "principal") -> None:
        """Incrementa contador de comentários coletados com sucesso."""
        CONTADOR_COLETA_COMENTARIOS.labels(status="sucesso", origem=origem).inc(quantidade)

    @staticmethod
    def registrar_erro(tipo_erro: str) -> None:
        """Incrementa contador de erros categorizados (ex: quota, rede, indisponivel)."""
        CONTADOR_COLETA_ERROS.labels(tipo_erro=tipo_erro).inc()

    @staticmethod
    def registrar_execucao_pipeline(
        duracao_segundos: float, canal: str = "geral", sucesso: bool = True
    ) -> None:
        """Registra a duração em segundos de cada execução individual do pipeline."""
        GAUGE_PIPELINE_ULTIMA_EXECUCAO.labels(canal=canal).set(duracao_segundos)
        status_label = "sucesso" if sucesso else "falha"
        HISTOGRAMA_PIPELINE_EXECUCAO.labels(status=status_label).observe(duracao_segundos)
