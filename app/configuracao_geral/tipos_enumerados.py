"""Tipos enumerados (Enums) canônicos do sistema analítico e MLOps."""

from enum import StrEnum


class TecnicaCluster(StrEnum):
    """Algoritmos de clusterização suportados pelo pipeline analítico."""

    KMEANS = "kmeans"
    DBSCAN = "dbscan"
    HDBSCAN = "hdbscan"


class JanelaTemporal(StrEnum):
    """Intervalos de janelas temporais analíticas suportadas."""

    SETE_DIAS = "7dias"
    QUINZE_DIAS = "15dias"
    TRINTA_DIAS = "30dias"


class StatusTendencia(StrEnum):
    """Classificação do comportamento temporal do tópico."""

    CRESCENDO = "crescendo"
    DECRESCENDO = "decrescendo"
    ESTAVEL = "estavel"
    NOVO = "novo"
    SEM_DADOS = "sem_dados"
    ESTATICO = "estatico"


class OrigemComentario(StrEnum):
    """Classificação de hierarquia do comentário no YouTube."""

    PRINCIPAL = "principal"
    RESPOSTA = "resposta"


class CamadaLakehouse(StrEnum):
    """Níveis da arquitetura medalhão no storage S3."""

    BRONZE = "bronze"
    PRATA = "prata"
    OURO = "ouro"


class TecnicaRepresentacao(StrEnum):
    """Técnicas de vetorização textual implementadas."""

    TFIDF = "tfidf"
    BERTIMBAU = "bertimbau"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    HIBRIDA = "hibrida"
    COUNT = "count"



class TecnicaReducao(StrEnum):
    """Algoritmos de redução de dimensionalidade suportados."""

    PCA = "pca"
    SVD = "svd"
    TSNE = "tsne"
    UMAP = "umap"


class PeriodicidadeColeta(StrEnum):
    """Periodicidade programada do ciclo de ingestão."""

    DIARIA = "diaria"
    SEMANAL = "semanal"


class StatusSaude(StrEnum):
    """Status operacional do serviço e containers."""

    SAUDAVEL = "saudavel"
    DEGRADADO = "degradado"


class MotorProcessamento(StrEnum):
    """Motores de processamento e manipulação tabular suportados no pipeline."""

    PANDAS = "pandas"
    POLARS = "polars"


class NormaVetorizacao(StrEnum):
    """Estratégias de normalização vetorial L1 e L2."""

    L1 = "l1"
    L2 = "l2"


class DispositivoExecucao(StrEnum):
    """Dispositivos de inferência para modelos de deep learning / transformers."""

    CPU = "cpu"
    CUDA = "cuda"


class MetricaDistancia(StrEnum):
    """Métricas de distância e similaridade suportadas para agrupamento e projeção."""

    COSINE = "cosine"
    EUCLIDEAN = "euclidean"


class InicializacaoKMeans(StrEnum):
    """Estratégias de inicialização de centróides no KMeans."""

    KMEANS_PLUS_PLUS = "k-means++"
    RANDOM = "random"


class MetodoSelecaoCluster(StrEnum):
    """Métodos de seleção de clusters no HDBSCAN."""

    EOM = "eom"
    LEAF = "leaf"


class AlgoritmoVizinhos(StrEnum):
    """Algoritmos de busca de vizinhos mais próximos no DBSCAN."""

    AUTO = "auto"
    BALL_TREE = "ball_tree"
    KD_TREE = "kd_tree"
    BRUTE = "brute"


class GranularidadeTendencia(StrEnum):
    """Granularidade de análise da série temporal de tópicos."""

    DIARIA = "diaria"
    JANELA = "janela"


class TipoPersistencia(StrEnum):
    """Mecanismos de armazenamento suportados para o lakehouse."""

    S3 = "s3"
    LOCAL = "local"


class TipoFonteDados(StrEnum):
    """Mecanismos suportados de ingestão e extração de dados."""

    YOUTUBE = "youtube"
    CSV = "csv"
    PARQUET = "parquet"
    JSONL = "jsonl"
    LOCAL = "local"


class TipoProvedorVisualizacao(StrEnum):
    """Provedores de dashboards e visualização operacional suportados."""

    GRAFANA = "grafana"
    NENHUM = "nenhum"
    CUSTOM = "custom"



