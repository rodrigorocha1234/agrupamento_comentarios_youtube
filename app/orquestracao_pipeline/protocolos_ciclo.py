"""Protocolos estruturais e interfaces para desacoplamento da orquestração do pipeline."""

from typing import Protocol, runtime_checkable

from app.agrupamento_modelos.avaliador_qualidade import MetricasAgrupamento
from app.coleta_youtube.modelos_coleta import ComentarioColetado, MetadadosVideo
from app.gestao_dados.camada_ouro import RegistroTopicoOuro


@runtime_checkable
class ProtocoloExecutorCiclo(Protocol):
    """Protocolo estrutural para executores do ciclo completo do pipeline."""

    def executar_ciclo_canal(self, id_canal: str) -> dict[str, int]:
        """Executa a sequência completa de coleta, processamento, ML e lakehouse para um canal."""
        ...


@runtime_checkable
class ProtocoloExtratorComentarios(Protocol):
    """Protocolo estrutural para extração de vídeos e comentários de canais."""

    def extrair_canal_completo(
        self,
        id_canal: str,
        dias_retroativos: int = 7,
        incluir_respostas: bool = True,
        limite_videos: int | None = None,
        tamanho_pagina: int = 100,
    ) -> tuple[list[MetadadosVideo], list[ComentarioColetado]]: ...

    def obter_detalhes_canal(self, id_canal: str) -> tuple[str, str]: ...


@runtime_checkable
class ProtocoloCamadaBronze(Protocol):
    """Protocolo estrutural para a camada Bronze do Lakehouse."""

    def gravar_lote_comentarios(
        self,
        id_canal: str,
        id_video: str,
        comentarios: list[ComentarioColetado],
    ) -> str: ...


@runtime_checkable
class ProtocoloCamadaPrata(Protocol):
    """Protocolo estrutural para a camada Prata do Lakehouse."""

    def gravar_snapshot_comentarios(
        self,
        id_canal: str,
        id_video: str,
        novos_comentarios: list[ComentarioColetado],
    ) -> str: ...


@runtime_checkable
class ProtocoloCamadaOuro(Protocol):
    """Protocolo estrutural para a camada Ouro do Lakehouse."""

    def gravar_catalogo_videos(
        self,
        id_canal: str,
        nome_canal: str,
        videos: list[tuple[str, str]],
    ) -> str: ...

    def gravar_topicos_video(
        self,
        id_canal: str,
        id_video: str,
        tecnica: str,
        topicos: list[RegistroTopicoOuro],
        janela: str = "",
    ) -> str: ...

    def gravar_topicos_canal_consolidado(
        self,
        id_canal: str,
        tecnica: str,
        topicos: list[RegistroTopicoOuro],
        janela: str = "",
    ) -> str: ...


@runtime_checkable
class ProtocoloLematizador(Protocol):
    """Protocolo estrutural para lematização e processamento morfológico."""

    def processar_texto(self, texto: str) -> list[str]: ...


@runtime_checkable
class ProtocoloRotuladorTopicos(Protocol):
    """Protocolo estrutural para rotulagem não-LLM de tópicos por cluster."""

    def rotular_cluster(
        self,
        lemas_cluster: list[list[str]],
        lemas_globais: list[list[str]],
    ) -> str: ...


@runtime_checkable
class ProtocoloCalculadorTendencias(Protocol):
    """Protocolo estrutural para cálculo de tendências temporais em vídeos."""

    def calcular_tendencias_video(
        self,
        id_canal: str,
        id_video: str,
        tecnica: str,
        topicos_por_comentario: dict[str, str],
        comentarios: list[ComentarioColetado],
    ) -> list[RegistroTopicoOuro]: ...


@runtime_checkable
class ProtocoloAgregadorVisoes(Protocol):
    """Protocolo estrutural para consolidação de visões por canal."""

    def consolidar_canal(
        self,
        id_canal: str,
        tecnica: str,
        topicos_dos_videos: list[RegistroTopicoOuro],
        janela: str = "",
    ) -> list[RegistroTopicoOuro]: ...


@runtime_checkable
class ProtocoloRastreadorExperimentos(Protocol):
    """Protocolo estrutural para rastreamento de experimentos e registro de modelos."""

    def registrar_execucao(
        self,
        nome_experimento: str,
        tecnica: str,
        parametros: dict[str, object],
        metricas: MetricasAgrupamento,
        uri_manifesto_s3: str,
        modelo_sklearn: object | None = None,
        nome_modelo_registry: str | None = None,
        nome_artefato_modelo: str = "modelo",
    ) -> str: ...


__all__ = [
    "ProtocoloExecutorCiclo",
    "ProtocoloExtratorComentarios",
    "ProtocoloCamadaBronze",
    "ProtocoloCamadaPrata",
    "ProtocoloCamadaOuro",
    "ProtocoloLematizador",
    "ProtocoloRotuladorTopicos",
    "ProtocoloCalculadorTendencias",
    "ProtocoloAgregadorVisoes",
    "ProtocoloRastreadorExperimentos",
]
