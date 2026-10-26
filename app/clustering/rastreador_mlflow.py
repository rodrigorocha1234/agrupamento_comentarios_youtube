"""Observador de experimentos com integração ao MLflow Server remoto."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import override

import mlflow
from mlflow.tracking import MlflowClient
from sklearn.base import BaseEstimator

from app.conf_yaml import ConfigMLflowInfo
from app.contratos.observador import ProtocoloObservadorExperimento


class RastreadorMLflow(ProtocoloObservadorExperimento):
    """Implementa o padrão Observer reportando métricas, parâmetros e artefatos ao MLflow."""

    def __init__(
        self,
        config: ConfigMLflowInfo,
        cliente_mlflow: MlflowClient | None = None,
    ) -> None:
        self._config = config
        self._habilitado = config.habilitado
        self._tracking_uri = config.tracking_uri
        self._nome_experimento = config.experiment_name

        if self._habilitado:
            if self._tracking_uri:
                mlflow.set_tracking_uri(self._tracking_uri)
            mlflow.set_experiment(self._nome_experimento)
            self._cliente = cliente_mlflow or MlflowClient()
        else:
            self._cliente = None

    @contextmanager
    def iniciar_execucao(
        self,
        nome_execucao: str | None = None,
        tags_iniciais: dict[str, str] | None = None,
    ) -> Generator[mlflow.ActiveRun | None, None, None]:
        """Abre uma execução ativa do MLflow no contexto gerenciado."""
        if not self._habilitado:
            yield None
            return

        tags = dict(self._config.tags)
        if tags_iniciais:
            tags.update(tags_iniciais)

        with mlflow.start_run(run_name=nome_execucao, tags=tags) as run:
            yield run

    @override
    def registrar_parametros(self, parametros: dict[str, str | int | float | bool]) -> None:
        """Registra parâmetros escalares da configuração no MLflow."""
        if not self._habilitado or not self._config.registrar_parametros:
            return
        parametros_formatados = {k: str(v) for k, v in parametros.items()}
        mlflow.log_params(parametros_formatados)

    @override
    def registrar_metricas(self, metricas: dict[str, float]) -> None:
        """Registra métricas analíticas e operacionais no MLflow."""
        if not self._habilitado or not self._config.registrar_metricas:
            return
        mlflow.log_metrics(metricas)

    @override
    def registrar_tags(self, tags: dict[str, str]) -> None:
        """Registra tags contextuais da execução."""
        if not self._habilitado:
            return
        mlflow.set_tags(tags)

    @override
    def registrar_artefato(self, caminho_local: str, subpasta_destino: str | None = None) -> None:
        """Registra artefatos analíticos (ex: relatórios HTML Plotly, JSONs)."""
        if not self._habilitado or not self._config.registrar_artefatos:
            return
        mlflow.log_artifact(caminho_local, artifact_path=subpasta_destino)

    def registrar_modelo_sklearn(
        self,
        modelo: BaseEstimator,
        nome_artefato: str = "modelo_clustering",
    ) -> None:
        """Registra o estimador do scikit-learn como artefato oficial de modelo do MLflow."""
        if not self._habilitado or not self._config.registrar_modelo:
            return
        mlflow.sklearn.log_model(modelo, artifact_path=nome_artefato)  # type: ignore[attr-defined]
