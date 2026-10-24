"""Adaptador concreto para publicação de telemetria e artefatos no servidor MLflow."""

import json
import logging
from collections.abc import Mapping
from typing import final, override

import mlflow
import numpy as np

from app.integracao_mlflow.observador_treinamento import ObservadorTreinamento

_logger = logging.getLogger(__name__)


@final
class ObservadorMlflow(ObservadorTreinamento):
    """Observer concreto para registro de execuções de treinamento no MLflow."""

    def __init__(
        self,
        tracking_uri: str = "http://localhost:5000",
        falha_silenciosa: bool = True,
    ) -> None:
        self._tracking_uri = tracking_uri
        self._falha_silenciosa = falha_silenciosa
        self._run_ativa: bool = False
        self._configurar_cliente()

    def _configurar_cliente(self) -> None:
        """Define o URI de rastreamento do MLflow."""
        try:
            mlflow.set_tracking_uri(self._tracking_uri)
        except Exception as erro:
            if not self._falha_silenciosa:
                raise
            _logger.warning("Falha ao definir tracking_uri do MLflow: %s", erro)

    @override
    def registrar_inicio(
        self,
        nome_experimento: str,
        nome_execucao: str,
        parametros: Mapping[str, object],
        tags: Mapping[str, str],
    ) -> None:
        """Inicia uma run no experimento especificado e registra metadados iniciais."""
        try:
            mlflow.set_experiment(nome_experimento)
            mlflow.start_run(run_name=nome_execucao)
            self._run_ativa = True

            # Converte valores dos parâmetros para formatos compatíveis com MLflow
            params_sanitizados: dict[str, str | int | float] = {}
            for k, v in parametros.items():
                if isinstance(v, (int, float, str, bool)):
                    params_sanitizados[k] = v if not isinstance(v, bool) else str(v)
                else:
                    params_sanitizados[k] = json.dumps(v, ensure_ascii=False)

            if params_sanitizados:
                mlflow.log_params(params_sanitizados)

            if tags:
                mlflow.set_tags(dict(tags))
        except Exception as erro:
            if not self._falha_silenciosa:
                raise
            _logger.warning("Erro ao iniciar execução no MLflow: %s", erro)

    @override
    def registrar_metricas(
        self,
        metricas: Mapping[str, float],
        etapa: int = 0,
    ) -> None:
        """Registra métricas escalares no MLflow."""
        if not self._run_ativa:
            return
        try:
            # Filtra valores numéricos finitos válidos
            metricas_validas: dict[str, float] = {
                k: float(v) for k, v in metricas.items() if np.isfinite(v)
            }
            if metricas_validas:
                mlflow.log_metrics(metricas_validas, step=etapa)
        except Exception as erro:
            if not self._falha_silenciosa:
                raise
            _logger.warning("Erro ao registrar métricas no MLflow: %s", erro)

    @override
    def registrar_artefato_texto(
        self,
        conteudo: str,
        nome_arquivo: str,
    ) -> None:
        """Publica um arquivo textual no repositório de artefatos."""
        if not self._run_ativa:
            return
        try:
            mlflow.log_text(conteudo, artifact_file=nome_arquivo)
        except Exception as erro:
            if not self._falha_silenciosa:
                raise
            _logger.warning("Erro ao registrar artefato textual no MLflow: %s", erro)

    @override
    def registrar_artefato_dicionario(
        self,
        dados: Mapping[str, object],
        nome_arquivo: str,
    ) -> None:
        """Publica um dicionário como JSON nos artefatos."""
        if not self._run_ativa:
            return
        try:
            conteudo_json = json.dumps(dados, indent=2, ensure_ascii=False)
            mlflow.log_text(conteudo_json, artifact_file=nome_arquivo)
        except Exception as erro:
            if not self._falha_silenciosa:
                raise
            _logger.warning("Erro ao registrar artefato JSON no MLflow: %s", erro)

    @override
    def registrar_distribuicao_clusters(
        self,
        rotulos: np.ndarray,
    ) -> None:
        """Calcula e registra a contagem e proporção de pontos por cluster."""
        if not self._run_ativa or len(rotulos) == 0:
            return
        try:
            valores, contagens = np.unique(rotulos, return_counts=True)
            total = float(len(rotulos))
            metricas_clusters: dict[str, float] = {}

            for val, qtd in zip(valores, contagens, strict=False):
                nome_rotulo = f"cluster_{val}" if val != -1 else "cluster_ruido"
                metricas_clusters[f"{nome_rotulo}_tamanho"] = float(qtd)
                metricas_clusters[f"{nome_rotulo}_proporcao"] = float(qtd) / total

            mlflow.log_metrics(metricas_clusters)
        except Exception as erro:
            if not self._falha_silenciosa:
                raise
            _logger.warning(
                "Erro ao registrar distribuição de clusters no MLflow: %s", erro
            )

    @override
    def registrar_fim(
        self,
        status: str = "FINISHED",
    ) -> None:
        """Encerra a run ativa no MLflow."""
        if not self._run_ativa:
            return
        try:
            mlflow.end_run(status=status)
        except Exception as erro:
            if not self._falha_silenciosa:
                raise
            _logger.warning("Erro ao encerrar run no MLflow: %s", erro)
        finally:
            self._run_ativa = False
