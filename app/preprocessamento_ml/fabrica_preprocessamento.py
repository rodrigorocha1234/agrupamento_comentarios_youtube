"""Fábrica de montagem do pipeline de pré-processamento declarativo."""

from typing import final

from app.preprocessamento_ml.pipeline_composto import (
    PipelineComposto,
    TransformadorPreprocessamento,
)
from app.preprocessamento_ml.redutor_dimensionalidade import RedutorDimensionalidade
from app.preprocessamento_ml.transformador_escalonador import TransformadorEscalonador
from app.preprocessamento_ml.transformador_imputador import TransformadorImputador


@final
class FabricaPreprocessamento:
    """Instancia o PipelineComposto a partir das especificações de configuração."""

    def construir_pipeline(
        self,
        imputacao_ativada: bool = True,
        tecnica_imputacao: str = "median",
        escalonamento_ativado: bool = True,
        tecnica_escalonamento: str = "standard_scaler",
        reducao_ativada: bool = False,
        tecnica_reducao: str = "pca",
        n_componentes: int = 2,
    ) -> PipelineComposto:
        """Monta a sequência de transformadores ordenada."""
        etapas: list[TransformadorPreprocessamento] = []

        if imputacao_ativada:
            etapas.append(TransformadorImputador(estrategia=tecnica_imputacao))

        if escalonamento_ativado:
            etapas.append(TransformadorEscalonador(tecnica=tecnica_escalonamento))

        if reducao_ativada:
            etapas.append(
                RedutorDimensionalidade(
                    tecnica=tecnica_reducao, n_componentes=n_componentes
                )
            )

        return PipelineComposto(etapas)
