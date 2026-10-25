"""Orquestrador do treinamento de clustering, cálculo de métricas e integração MLflow/Lakehouse."""

from dataclasses import dataclass
from typing import Final

import numpy as np
import pandas as pd

from app.clustering.avaliador_clusters import AvaliadorClusters, MetricasClustering
from app.clustering.fabrica_clustering import FabricaClustering
from app.clustering.rastreador_mlflow import RastreadorMLflow
from app.conf_yaml import ConfigClusteringInfo, ConfigMLflowInfo
from app.contratos.motor_clustering import ProtocoloMotorClustering
from app.contratos.repositorio import ProtocoloRepositorioLakehouse
from app.excecoes import ErroClustering

SUFIXO_VISAO_CLUSTERS: Final[str] = "clusters"


@dataclass(frozen=True)
class ResultadoClustering:
    """Encapsula o resultado completo da execução do algoritmo de clustering."""

    motor: ProtocoloMotorClustering
    rotulos: list[int]
    metricas: MetricasClustering
    dados_com_rotulos: pd.DataFrame
    run_id: str | None = None
    uri_gold_clusters: str = ""


class ExecutorClustering:
    """Orquestra o ciclo de vida do treinamento de clustering e persistência analítica."""

    def __init__(
        self,
        config_clustering: ConfigClusteringInfo,
        config_mlflow: ConfigMLflowInfo | None = None,
        rastreador: RastreadorMLflow | None = None,
    ) -> None:
        self._config_clustering = config_clustering
        self._config_mlflow = config_mlflow

        if rastreador is not None:
            self._rastreador = rastreador
        elif config_mlflow is not None:
            self._rastreador = RastreadorMLflow(config_mlflow)
        else:
            self._rastreador = None

    def executar(
        self,
        matriz_treino: np.ndarray | pd.DataFrame,
        metadados: pd.DataFrame | None = None,
        identificador: str | int | None = None,
        repositorio: ProtocoloRepositorioLakehouse | None = None,
        tags_execucao: dict[str, str] | None = None,
    ) -> ResultadoClustering:
        """Executa ajuste do algoritmo, avaliação métrica, tracking e persistência Gold."""
        if isinstance(matriz_treino, pd.DataFrame):
            matriz_np = np.asarray(matriz_treino.to_numpy(dtype=np.float64), dtype=np.float64)
        else:
            matriz_np = np.asarray(matriz_treino, dtype=np.float64)

        if matriz_np.ndim != 2 or matriz_np.shape[0] == 0:
            raise ErroClustering("Matriz de treino inválida para execução do clustering.")

        motor = FabricaClustering.criar(self._config_clustering)
        motor.ajustar(matriz_np)
        rotulos = motor.obter_rotulos()

        metricas = AvaliadorClusters.avaliar(matriz_np, rotulos)

        if metadados is not None and not metadados.empty:
            df_clusterizado = metadados.copy()
        else:
            df_clusterizado = pd.DataFrame(index=range(len(rotulos)))

        df_clusterizado["cluster"] = rotulos

        run_id: str | None = None

        if self._rastreador is not None:
            nome_run = f"clustering_{self._config_clustering.algoritmo}"
            tags_completas = {"algoritmo": self._config_clustering.algoritmo}
            if tags_execucao:
                tags_completas.update(tags_execucao)

            with self._rastreador.iniciar_execucao(
                nome_execucao=nome_run,
                tags_iniciais=tags_completas,
            ) as run:
                if run is not None and hasattr(run, "info"):
                    run_id = getattr(run.info, "run_id", None)

                params_log: dict[str, str | int | float | bool] = {
                    "algoritmo": self._config_clustering.algoritmo,
                    "motor": self._config_clustering.motor,
                }
                if self._config_clustering.algoritmo == "kmeans":
                    params_log.update(self._config_clustering.algoritmos.kmeans.model_dump())
                elif self._config_clustering.algoritmo == "dbscan":
                    params_log.update(self._config_clustering.algoritmos.dbscan.model_dump())
                elif self._config_clustering.algoritmo == "hdbscan":
                    params_log.update(self._config_clustering.algoritmos.hdbscan.model_dump())
                self._rastreador.registrar_parametros(params_log)

                # Métricas
                self._rastreador.registrar_metricas(metricas.para_dicionario())

                # Registro de modelo caso aplicável
                modelo_interno = getattr(motor, "_modelo", None)
                if modelo_interno is not None:
                    self._rastreador.registrar_modelo_sklearn(modelo_interno)

        uri_gold_clusters = ""
        if repositorio is not None and identificador is not None:
            uri_gold_clusters = repositorio.gravar_gold(
                identificador=identificador,
                dados=df_clusterizado,
                sufixo_visao=SUFIXO_VISAO_CLUSTERS,
            )

        return ResultadoClustering(
            motor=motor,
            rotulos=rotulos,
            metricas=metricas,
            dados_com_rotulos=df_clusterizado,
            run_id=run_id,
            uri_gold_clusters=uri_gold_clusters,
        )
