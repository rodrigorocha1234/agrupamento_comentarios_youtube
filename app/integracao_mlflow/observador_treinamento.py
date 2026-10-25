"""Protocolo tipado do Observer de MLOps para notificações do ciclo de treinamento."""

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

import numpy as np

from app.dominio_contratos.modelos_dados import TipoDadoJson, TipoParametroAlgoritmo


@runtime_checkable
class ObservadorTreinamento(Protocol):
    """Protocolo GoF Observer para telemetria, logs de métricas e artefatos no MLflow."""

    def registrar_inicio(
        self,
        nome_experimento: str,
        nome_execucao: str,
        parametros: Mapping[str, TipoParametroAlgoritmo],
        tags: Mapping[str, str],
    ) -> None:
        """Notifica o início de uma sessão ou run de treinamento."""
        ...

    def registrar_metricas(
        self,
        metricas: Mapping[str, float],
        etapa: int = 0,
    ) -> None:
        """Registra métricas escalares no servidor de rastreamento."""
        ...

    def registrar_artefato_texto(
        self,
        conteudo: str,
        nome_arquivo: str,
    ) -> None:
        """Grava um artefato textual (ex: JSON, YAML, sumário estatístico)."""
        ...

    def registrar_artefato_dicionario(
        self,
        dados: Mapping[str, TipoDadoJson],
        nome_arquivo: str,
    ) -> None:
        """Grava um artefato serializável a partir de um dicionário."""
        ...

    def registrar_distribuicao_clusters(
        self,
        rotulos: np.ndarray,
    ) -> None:
        """Registra métricas agregadas de volumetria por rótulo de cluster."""
        ...

    def registrar_fim(
        self,
        status: str = "FINISHED",
    ) -> None:
        """Finaliza a execução ativa no rastreador."""
        ...
