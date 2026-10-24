"""Etapa de escalonamento numérico para algoritmos de clustering sensíveis a distância."""

from typing import Self, final

import numpy as np
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler


@final
class TransformadorEscalonador:
    """Padroniza ou normaliza matrizes numéricas com suporte a diferentes técnicas."""

    def __init__(self, tecnica: str = "standard_scaler") -> None:
        self._tecnica = tecnica.lower()
        if self._tecnica == "robust_scaler":
            self._escalonador = RobustScaler()
        elif self._tecnica == "min_max_scaler":
            self._escalonador = MinMaxScaler()
        else:
            self._escalonador = StandardScaler()
        self._ajustado = False

    def ajustar(self, matriz_x: np.ndarray) -> Self:
        """Calcula parâmetros estatísticos de escala (média, desvio, IQR) no treino."""
        self._escalonador.fit(matriz_x)
        self._ajustado = True
        return self

    def transformar(self, matriz_x: np.ndarray) -> np.ndarray:
        """Aplica a escala na matriz numérica."""
        if not self._ajustado:
            raise RuntimeError(
                "O escalonador deve ser ajustado antes de transformar os dados."
            )
        resultado = self._escalonador.transform(matriz_x)
        if isinstance(resultado, np.ndarray):
            return resultado
        return np.asarray(resultado, dtype=np.float64)
