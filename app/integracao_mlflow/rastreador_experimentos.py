import importlib
from typing import cast
import mlflow
from mlflow.entities import Run

from app.agrupamento_modelos.avaliador_qualidade import MetricasAgrupamento


class RastreadorExperimentosErro(Exception):
    """Exceção levantada em falhas de comunicação com o MLflow Tracking."""


class RastreadorExperimentos:
    """Gerencia execuções (runs) no MLflow registrando métricas, parâmetros e manifestos S3."""

    def __init__(self, tracking_uri: str = "http://127.0.0.1:5000") -> None:
        self._tracking_uri: str = tracking_uri
        try:
            mlflow.set_tracking_uri(tracking_uri)
        except Exception:
            pass

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
    ) -> str:
        """Cria uma run no MLflow, grava parâmetros, métricas, tags e salva o modelo treinado."""
        try:
            mlflow.set_experiment(nome_experimento)
            with mlflow.start_run(run_name=f"agrupamento_{tecnica}") as run:
                run_obj = cast(Run, run)
                run_id = run_obj.info.run_id

                # Log de parâmetros
                params_str: dict[str, str] = {
                    k: str(v) for k, v in parametros.items()
                }
                params_str["tecnica"] = tecnica
                mlflow.log_params(params_str)

                # Log de métricas
                metricas_dict: dict[str, float] = {
                    "quantidade_clusters": float(metricas.quantidade_clusters),
                    "fracao_ruido": float(metricas.fracao_ruido),
                }
                if metricas.pontuacao_silhueta is not None:
                    metricas_dict["pontuacao_silhueta"] = metricas.pontuacao_silhueta
                if metricas.indice_davies_bouldin is not None:
                    metricas_dict["indice_davies_bouldin"] = metricas.indice_davies_bouldin
                if metricas.pontuacao_calinski_harabasz is not None:
                    metricas_dict["pontuacao_calinski_harabasz"] = metricas.pontuacao_calinski_harabasz

                mlflow.log_metrics(metricas_dict)

                # Log de tags de proveniência do Data Lake S3
                mlflow.set_tags(
                    {
                        "s3_manifesto_uri": uri_manifesto_s3,
                        "tecnica": tecnica,
                    }
                )

                # Salvamento de artefato do modelo treinado no MLflow
                if modelo_sklearn is not None:
                    try:
                        mlflow_sklearn: object = importlib.import_module("mlflow.sklearn")
                        log_model_fn = getattr(mlflow_sklearn, "log_model", None)
                        if callable(log_model_fn):
                            log_model_fn(
                                sk_model=modelo_sklearn,
                                artifact_path=nome_artefato_modelo,
                            )
                        if nome_modelo_registry:
                            mlflow.register_model(
                                model_uri=f"runs:/{run_id}/{nome_artefato_modelo}",
                                name=nome_modelo_registry,
                            )
                    except Exception:
                        pass

                return run_id
        except Exception as erro:
            raise RastreadorExperimentosErro(
                f"Falha ao registrar execução no MLflow em {self._tracking_uri}: {erro}"
            ) from erro
