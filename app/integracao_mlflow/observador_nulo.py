"""Implementação Null Object para execução desacoplada quando MLflow estiver inativo."""

from collections.abc import Mapping
from typing import final, override

import numpy as np

from app.integracao_mlflow.observador_treinamento import ObservadorTreinamento


@final
class ObservadorNulo(ObservadorTreinamento):
    """Null Object GoF que descarta chamadas de telemetria sem impacto colateral."""

    @override
    def registrar_inicio(
        self,
        nome_experimento: str,
        nome_execucao: str,
        parametros: Mapping[str, object],
        tags: Mapping[str, str],
    ) -> None:
        pass

    @override
    def registrar_metricas(
        self,
        metricas: Mapping[str, float],
        etapa: int = 0,
    ) -> None:
        pass

    @override
    def registrar_artefato_texto(
        self,
        conteudo: str,
        nome_arquivo: str,
    ) -> None:
        pass

    @override
    def registrar_artefato_dicionario(
        self,
        dados: Mapping[str, object],
        nome_arquivo: str,
    ) -> None:
        pass

    @override
    def registrar_distribuicao_clusters(
        self,
        rotulos: np.ndarray,
    ) -> None:
        pass

    @override
    def registrar_fim(
        self,
        status: str = "FINISHED",
    ) -> None:
        pass
