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
    COUNT = "count"


class TecnicaReducao(StrEnum):
    """Algoritmos de redução de dimensionalidade suportados."""

    PCA = "pca"
    SVD = "svd"
    TSNE = "tsne"


class PeriodicidadeColeta(StrEnum):
    """Periodicidade programada do ciclo de ingestão."""

    DIARIA = "diaria"
    SEMANAL = "semanal"


class StatusSaude(StrEnum):
    """Status operacional do serviço e containers."""

    SAUDAVEL = "saudavel"
    DEGRADADO = "degradado"
