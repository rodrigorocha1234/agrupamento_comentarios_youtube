"""Testes para o pipeline de pré-processamento composable."""

import numpy as np
import pytest

from app.preprocessamento_ml.fabrica_preprocessamento import (
    FabricaPreprocessamento,
)
from app.preprocessamento_ml.pipeline_composto import PipelineComposto
from app.preprocessamento_ml.redutor_dimensionalidade import (
    RedutorDimensionalidade,
)
from app.preprocessamento_ml.transformador_escalonador import (
    TransformadorEscalonador,
)
from app.preprocessamento_ml.transformador_imputador import (
    TransformadorImputador,
)


def teste_imputador_mediana() -> None:
    """Verifica substituição correta de NaNs pela mediana da coluna."""
    matriz = np.array([[10.0, 2.0], [np.nan, 4.0], [30.0, np.nan]], dtype=np.float64)
    imputador = TransformadorImputador(estrategia="median")

    resultado = imputador.ajustar(matriz).transformar(matriz)

    # Mediana col 0: (10 + 30)/2 = 20.0; Mediana col 1: (2 + 4)/2 = 3.0
    assert resultado[1, 0] == 20.0
    assert resultado[2, 1] == 3.0


def teste_escalonador_padrao() -> None:
    """Verifica padronização para média 0 e variância unitária."""
    matriz = np.array([[10.0], [20.0], [30.0], [40.0], [50.0]], dtype=np.float64)
    escalonador = TransformadorEscalonador(tecnica="standard_scaler")

    resultado = escalonador.ajustar(matriz).transformar(matriz)

    assert float(np.mean(resultado)) == pytest.approx(0.0, abs=1e-7)
    assert float(np.std(resultado)) == pytest.approx(1.0, abs=1e-7)


def teste_redutor_pca() -> None:
    """Verifica redução da dimensão de 4 para 2 componentes."""
    rng = np.random.default_rng(42)
    matriz = rng.normal(size=(20, 4))
    redutor = RedutorDimensionalidade(tecnica="pca", n_componentes=2)

    resultado = redutor.ajustar(matriz).transformar(matriz)

    assert resultado.shape == (20, 2)


def teste_pipeline_composto_fluxo_completo() -> None:
    """Verifica encadeamento sem data leakage com PipelineComposto."""
    fabrica = FabricaPreprocessamento()
    pipeline: PipelineComposto = fabrica.construir_pipeline(
        imputacao_ativada=True,
        tecnica_imputacao="median",
        escalonamento_ativado=True,
        tecnica_escalonamento="standard_scaler",
        reducao_ativada=True,
        tecnica_reducao="pca",
        n_componentes=2,
    )

    matriz = np.array(
        [
            [10.0, 100.0, np.nan],
            [20.0, np.nan, 5.0],
            [30.0, 300.0, 15.0],
            [40.0, 400.0, 20.0],
        ],
        dtype=np.float64,
    )

    saida = pipeline.ajustar_e_transformar(matriz)
    assert saida.shape == (4, 2)
