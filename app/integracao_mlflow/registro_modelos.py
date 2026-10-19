"""Gerenciamento de modelos no MLflow Model Registry."""

import mlflow


class RegistroModelosErro(Exception):
    """Exceção levantada em falhas no registro de modelos."""


class RegistroModelos:
    """Gerencia o registro de modelos homologados e sua transição de versões."""

    def __init__(self, tracking_uri: str = "http://127.0.0.1:5000") -> None:
        self._tracking_uri: str = tracking_uri
        try:
            mlflow.set_tracking_uri(tracking_uri)
        except Exception:
            pass

    def registrar_versao_modelo(
        self,
        run_id: str,
        nome_modelo: str,
        caminho_artefato: str = "modelo",
    ) -> str:
        """Registra a versão do modelo a partir de uma run executada."""
        try:
            modelo_uri = f"runs:/{run_id}/{caminho_artefato}"
            versao = mlflow.register_model(model_uri=modelo_uri, name=nome_modelo)
            return str(versao.version)
        except Exception as erro:
            raise RegistroModelosErro(
                f"Erro ao registrar modelo '{nome_modelo}' no registry: {erro}"
            ) from erro
