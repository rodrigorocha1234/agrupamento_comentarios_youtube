"""Redução de dimensionalidade via TruncatedSVD (LSA)."""

from typing import cast
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD


class RedutorDimensionalidade:
    """Aplica decomposição por valores singulares para redução dimensional opcional."""

    def __init__(self, componentes: int = 100, random_state: int = 42) -> None:
        self._componentes: int = componentes
        self._random_state: int = random_state
        self._redutor: TruncatedSVD | None = None

    def ajustar_e_reduzir(self, matriz: csr_matrix | np.ndarray) -> np.ndarray:
        """Ajusta o redutor e retorna a matriz reduzida com dimensões controladas."""
        shape = matriz.shape
        n_amostras = shape[0] if shape else 0
        n_colunas = shape[1] if shape and len(shape) > 1 else 1
        n_comp = min(self._componentes, n_amostras - 1, n_colunas - 1)
        if n_comp < 2:
            # Não reduz caso o número de componentes viáveis seja insuficiente
            if isinstance(matriz, csr_matrix):
                return matriz.toarray()
            return matriz

        self._redutor = TruncatedSVD(n_components=n_comp, random_state=self._random_state)
        matriz_reduzida = self._redutor.fit_transform(matriz)
        return cast(np.ndarray, matriz_reduzida)

    def reduzir(self, matriz: csr_matrix | np.ndarray) -> np.ndarray:
        """Aplica a transformação ajustada em novos dados."""
        if self._redutor is None:
            if isinstance(matriz, csr_matrix):
                return matriz.toarray()
            return matriz
        resultado = self._redutor.transform(matriz)
        return cast(np.ndarray, resultado)
