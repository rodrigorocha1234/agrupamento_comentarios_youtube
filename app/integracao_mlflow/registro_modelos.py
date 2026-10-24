"""Gerenciamento de empacotamento, serialização e registro de pipelines e modelos no MLflow."""

import io
import json
import logging
from collections.abc import Sequence
from typing import final

import joblib
import mlflow

from app.agrupamento_modelos.capacidades_algoritmo import EstrategiaAgrupamento
from app.preprocessamento_ml.pipeline_composto import PipelineComposto

_logger = logging.getLogger(__name__)


@final
class RegistroModelos:
    """Gerencia a persistência desacoplada de pipelines ajustados e modelos de clustering."""

    def __init__(self, falha_silenciosa: bool = True) -> None:
        self._falha_silenciosa = falha_silenciosa

    def registrar_pipeline_completo(
        self,
        pipeline: PipelineComposto,
        algoritmo: EstrategiaAgrupamento,
        nomes_colunas_treino: Sequence[str],
        versao_dataset: str,
        hash_configuracao: str,
    ) -> None:
        """Serializa e registra os componentes ajustados como artefatos no MLflow."""
        try:
            # 1. Salva metadados de assinatura e linhagem
            metadados = {
                "versao_dataset": versao_dataset,
                "hash_configuracao": hash_configuracao,
                "algoritmo": algoritmo.capacidades.nome_algoritmo,
                "suporta_predicao_fora_da_amostra": algoritmo.capacidades.suporta_predicao_fora_da_amostra,
                "possui_centroides": algoritmo.capacidades.possui_centroides,
                "gera_ruido": algoritmo.capacidades.gera_ruido,
                "colunas_treinamento": list(nomes_colunas_treino),
            }
            mlflow.log_text(
                json.dumps(metadados, indent=2, ensure_ascii=False),
                artifact_file="metadados_modelo.json",
            )

            # 2. Serializa o pipeline de pré-processamento via joblib
            buffer_pipeline = io.BytesIO()
            joblib.dump(pipeline, buffer_pipeline)
            buffer_pipeline.seek(0)
            mlflow.log_artifact(
                local_path=self._escrever_temporario(
                    buffer_pipeline.getvalue(), "pipeline_preprocessamento.joblib"
                ),
                artifact_path="modelos",
            )

            # 3. Serializa o algoritmo de clustering
            buffer_algoritmo = io.BytesIO()
            joblib.dump(algoritmo, buffer_algoritmo)
            buffer_algoritmo.seek(0)
            mlflow.log_artifact(
                local_path=self._escrever_temporario(
                    buffer_algoritmo.getvalue(), "algoritmo_agrupamento.joblib"
                ),
                artifact_path="modelos",
            )

            # 4. Registra centroides se o algoritmo suportar
            centroides = algoritmo.obter_centroides()
            if centroides is not None:
                buffer_centroides = io.BytesIO()
                joblib.dump(centroides, buffer_centroides)
                buffer_centroides.seek(0)
                mlflow.log_artifact(
                    local_path=self._escrever_temporario(
                        buffer_centroides.getvalue(), "centroides.joblib"
                    ),
                    artifact_path="modelos",
                )

        except Exception as erro:
            if not self._falha_silenciosa:
                raise
            _logger.warning("Erro ao persistir modelos no MLflow: %s", erro)

    def _escrever_temporario(self, conteudo: bytes, nome_arquivo: str) -> str:
        """Escreve um arquivo temporário em disco para upload ao MLflow."""
        import os
        import tempfile

        caminho_dir = tempfile.gettempdir()
        caminho_completo = os.path.join(caminho_dir, nome_arquivo)
        with open(caminho_completo, "wb") as f:
            f.write(conteudo)
        return caminho_completo
