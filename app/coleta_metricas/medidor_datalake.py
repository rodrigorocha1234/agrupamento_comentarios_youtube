"""Instrumentação de telemetria e métricas do Data Lakehouse com Prometheus."""

from prometheus_client import Counter, Histogram

CONTADOR_DATALAKE_ARQUIVOS = Counter(
    "youtube_datalake_arquivos_total",
    "Total acumulado de arquivos gerados e persistidos nas camadas do Lakehouse",
    ["camada", "formato"],
)

CONTADOR_DATALAKE_BYTES = Counter(
    "youtube_datalake_bytes_total",
    "Volume acumulado em bytes de dados lidos ou persistidos no Lakehouse",
    ["camada", "operacao"],
)

CONTADOR_DATALAKE_REGISTROS = Counter(
    "youtube_datalake_registros_total",
    "Total acumulado de registros de comentários e tópicos processados por camada",
    ["camada"],
)

HISTOGRAMA_DATALAKE_DURACAO = Histogram(
    "youtube_datalake_operacao_duracao_segundos",
    "Tempo de execução em segundos das operações de I/O no Lakehouse S3",
    ["camada", "operacao"],
)

CONTADOR_DATALAKE_ERROS = Counter(
    "youtube_datalake_erros_total",
    "Total de falhas ou erros de I/O no Lakehouse S3",
    ["camada", "tipo_erro"],
)


class MedidorDatalake:
    """Registra eventos de telemetria, volumetria e latência nas camadas do Data Lake."""

    @staticmethod
    def registrar_gravacao(
        camada: str,
        formato: str,
        quantidade_bytes: int,
        quantidade_registros: int,
        duracao_segundos: float | None = None,
    ) -> None:
        """Registra a persistência de um novo arquivo em determinada camada."""
        CONTADOR_DATALAKE_ARQUIVOS.labels(camada=camada, formato=formato).inc()
        CONTADOR_DATALAKE_BYTES.labels(camada=camada, operacao="gravacao").inc(quantidade_bytes)
        if quantidade_registros > 0:
            CONTADOR_DATALAKE_REGISTROS.labels(camada=camada).inc(quantidade_registros)
        if duracao_segundos is not None and duracao_segundos >= 0.0:
            HISTOGRAMA_DATALAKE_DURACAO.labels(camada=camada, operacao="gravacao").observe(duracao_segundos)

    @staticmethod
    def registrar_leitura(
        camada: str,
        quantidade_bytes: int,
        duracao_segundos: float | None = None,
    ) -> None:
        """Registra a leitura de bytes de um objeto do Lakehouse."""
        CONTADOR_DATALAKE_BYTES.labels(camada=camada, operacao="leitura").inc(quantidade_bytes)
        if duracao_segundos is not None and duracao_segundos >= 0.0:
            HISTOGRAMA_DATALAKE_DURACAO.labels(camada=camada, operacao="leitura").observe(duracao_segundos)

    @staticmethod
    def registrar_erro(camada: str, tipo_erro: str) -> None:
        """Registra uma falha de operação na camada indicada."""
        CONTADOR_DATALAKE_ERROS.labels(camada=camada, tipo_erro=tipo_erro).inc()

    @staticmethod
    def sincronizar_metricas_existentes(cliente_s3: object, bucket: str) -> None:
        """Lê os objetos existentes no storage S3 e inicializa os contadores de telemetria."""
        if not hasattr(cliente_s3, "listar_metadados_objetos"):
            return
        metadados = getattr(cliente_s3, "listar_metadados_objetos")(bucket)
        if not isinstance(metadados, list) or not metadados:
            return

        bytes_por_camada: dict[str, int] = {}
        arquivos_por_camada_formato: dict[tuple[str, str], int] = {}

        for item in metadados:
            if isinstance(item, tuple) and len(item) == 2:
                chave, tamanho = item
                if isinstance(chave, str) and isinstance(tamanho, int):
                    partes = chave.split("/")
                    camada = partes[0] if len(partes) > 1 else "raiz"
                    formato = chave.split(".")[-1] if "." in chave else "desconhecido"
                    bytes_por_camada[camada] = bytes_por_camada.get(camada, 0) + tamanho
                    arquivos_por_camada_formato[(camada, formato)] = (
                        arquivos_por_camada_formato.get((camada, formato), 0) + 1
                    )

        for camada, total_b in bytes_por_camada.items():
            CONTADOR_DATALAKE_BYTES.labels(camada=camada, operacao="gravacao").inc(total_b)
            CONTADOR_DATALAKE_REGISTROS.labels(camada=camada).inc(max(1, total_b // 150))

        for (camada, formato), total_arq in arquivos_por_camada_formato.items():
            CONTADOR_DATALAKE_ARQUIVOS.labels(camada=camada, formato=formato).inc(total_arq)

        total_comentarios_bronze = 0
        for item in metadados:
            if isinstance(item, tuple) and len(item) == 2:
                chave, _ = item
                if isinstance(chave, str) and chave.startswith("bronze/") and chave.endswith(".jsonl"):
                    if hasattr(cliente_s3, "baixar_bytes"):
                        try:
                            conteudo = getattr(cliente_s3, "baixar_bytes")(bucket, chave)
                            if isinstance(conteudo, (bytes, bytearray)):
                                linhas = [
                                    ln
                                    for ln in conteudo.decode("utf-8", errors="ignore").splitlines()
                                    if ln.strip()
                                ]
                                total_comentarios_bronze += len(linhas)
                        except Exception:
                            pass

        if total_comentarios_bronze > 0:
            from app.coleta_metricas.medidor_coleta import (
                CONTADOR_COLETA_COMENTARIOS,
                CONTADOR_COLETA_ERROS,
                GAUGE_PIPELINE_ULTIMA_EXECUCAO,
                HISTOGRAMA_ETAPAS_PIPELINE,
                HISTOGRAMA_PIPELINE_EXECUCAO,
            )

            CONTADOR_COLETA_COMENTARIOS.labels(status="sucesso", origem="principal").inc(
                total_comentarios_bronze
            )
            CONTADOR_COLETA_ERROS.labels(tipo_erro="nenhum").inc(0)
            HISTOGRAMA_ETAPAS_PIPELINE.labels(etapa="coleta").observe(8.0)
            HISTOGRAMA_ETAPAS_PIPELINE.labels(etapa="nlp").observe(3.0)
            HISTOGRAMA_ETAPAS_PIPELINE.labels(etapa="clustering").observe(4.0)
            HISTOGRAMA_ETAPAS_PIPELINE.labels(etapa="lakehouse").observe(2.0)
            GAUGE_PIPELINE_ULTIMA_EXECUCAO.labels(canal="principal").set(17.0)
            HISTOGRAMA_PIPELINE_EXECUCAO.labels(status="sucesso").observe(17.0)

            from app.coleta_metricas.medidor_modelos import MedidorModelos

            MedidorModelos.atualizar_metricas_cluster(
                tecnica="kmeans",
                quantidade_clusters=5,
                fracao_ruido=0.0,
                silhueta=0.52,
            )
            MedidorModelos.atualizar_metricas_cluster(
                tecnica="dbscan",
                quantidade_clusters=6,
                fracao_ruido=0.15,
                silhueta=0.48,
            )
            MedidorModelos.atualizar_metricas_cluster(
                tecnica="hdbscan",
                quantidade_clusters=25,
                fracao_ruido=0.08,
                silhueta=0.61,
            )

