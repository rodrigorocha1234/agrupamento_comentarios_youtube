"""Redução dimensional opcional para pré-processamento ou projeção geométrica."""

from typing import Self, final

import numpy as np
from sklearn.decomposition import PCA, TruncatedSVD


@final
class RedutorDimensionalidade:
    """Projeta matrizes multidimensionais em subespaços reduzidos via PCA ou SVD."""

    def __init__(self, tecnica: str = "pca", n_componentes: int = 2) -> None:
        self._tecnica = tecnica.lower()
        self._n_componentes = n_componentes
        if self._tecnica == "truncated_svd":
            self._redutor = TruncatedSVD(n_components=n_componentes, random_state=42)
        else:
            self._redutor = PCA(n_components=n_componentes, random_state=42)
        self._ajustado = False

    def ajustar(self, matriz_x: np.ndarray) -> Self:
        """Ajusta os autovetores ou componentes principais exclusivamente no treino."""
        max_comps = min(matriz_x.shape[0], matriz_x.shape[1])
        if self._n_componentes > max_comps:
            raise ValueError(
                f"n_componentes ({self._n_componentes}) excede o limite dimensional ({max_comps})."
            )
        self._redutor.fit(matriz_x)
        self._ajustado = True
        return self

    def transformar(self, matriz_x: np.ndarray) -> np.ndarray:
        """Aplica a projeção nos componentes aprendidos."""
        if not self._ajustado:
            raise RuntimeError(
                "O redutor deve ser ajustado antes de transformar os dados."
            )
        resultado = self._redutor.transform(matriz_x)
        if isinstance(resultado, np.ndarray):
            return resultado
        return np.asarray(resultado, dtype=np.float64)
