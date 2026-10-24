"""Pipeline Composto (Composite GoF) para encadeamento ordenado de pré-processamento."""

from collections.abc import Sequence
from typing import Protocol, Self, final

import numpy as np


class TransformadorPreprocessamento(Protocol):
    """Protocolo comum para etapas de transformação numérica de pré-processamento."""

    def ajustar(self, matriz_x: np.ndarray) -> Self:
        """Ajusta parâmetros no conjunto de dados fornecido."""
        ...

    def transformar(self, matriz_x: np.ndarray) -> np.ndarray:
        """Aplica a transformação aprendida."""
        ...


@final
class PipelineComposto:
    """Encadeia transformadores de forma sequencial garantindo isolamento sem vazamento."""

    def __init__(self, etapas: Sequence[TransformadorPreprocessamento]) -> None:
        self._etapas = tuple(etapas)
        self._ajustado = False

    def ajustar(self, matriz_x: np.ndarray) -> Self:
        """Ajusta sequencialmente cada etapa propagando a transformação para a seguinte."""
        x_atual = matriz_x
        for etapa in self._etapas:
            etapa.ajustar(x_atual)
            x_atual = etapa.transformar(x_atual)
        self._ajustado = True
        return self

    def transformar(self, matriz_x: np.ndarray) -> np.ndarray:
        """Transforma a matriz através de todas as etapas já ajustadas."""
        if not self._ajustado and self._etapas:
            raise RuntimeError(
                "O PipelineComposto deve ser ajustado antes de transformar os dados."
            )
        x_atual = matriz_x
        for etapa in self._etapas:
            x_atual = etapa.transformar(x_atual)
        return x_atual

    def ajustar_e_transformar(self, matriz_x: np.ndarray) -> np.ndarray:
        """Convenção para fit e transform em única passada no treino."""
        self.ajustar(matriz_x)
        return self.transformar(matriz_x)
