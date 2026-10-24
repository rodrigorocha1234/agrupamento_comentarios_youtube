"""Etapa de imputação de valores ausentes para matrizes numéricas de clustering."""

from typing import Self, final

import numpy as np
from sklearn.impute import SimpleImputer


@final
class TransformadorImputador:
    """Aplica imputação estrita por mediana ou média sem vazamento de dados."""

    def __init__(self, estrategia: str = "median") -> None:
        self._estrategia = estrategia
        self._imputador = SimpleImputer(strategy=estrategia)
        self._ajustado = False

    def ajustar(self, matriz_x: np.ndarray) -> Self:
        """Ajusta as estatísticas de imputação exclusivamente no conjunto de treino."""
        self._imputador.fit(matriz_x)
        self._ajustado = True
        return self

    def transformar(self, matriz_x: np.ndarray) -> np.ndarray:
        """Aplica a substituição dos valores ausentes."""
        if not self._ajustado:
            raise RuntimeError(
                "O transformador imputador deve ser ajustado antes da transformação."
            )
        resultado = self._imputador.transform(matriz_x)
        if isinstance(resultado, np.ndarray):
            return resultado
        return np.asarray(resultado, dtype=np.float64)
