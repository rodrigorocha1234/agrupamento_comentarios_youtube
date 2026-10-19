"""Redução de dimensionalidade não-linear via UMAP para agrupamento semântico."""

from typing import cast
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.preprocessing import normalize


class RedutorUmap:
    """Aplica Uniform Manifold Approximation and Projection (UMAP) sobre espaços vetoriais."""

    def __init__(
        self,
        componentes: int = 5,
        n_vizinhos: int = 15,
        distancia_minima: float = 0.0,
        metrica: str = "cosine",
        random_state: int = 42,
        norma: str | None = None,
    ) -> None:
        self._componentes: int = max(2, componentes)
        self._n_vizinhos: int = max(2, n_vizinhos)
        self._distancia_minima: float = max(0.0, distancia_minima)
        self._metrica: str = metrica
        self._random_state: int = random_state
        self._norma: str | None = norma
        self._redutor: object | None = None

    @property
    def componentes(self) -> int:
        """Quantidade alvo de dimensões reduzidas."""
        return self._componentes

    @property
    def n_vizinhos(self) -> int:
        """Tamanho da vizinhança local para balanceamento local vs global."""
        return self._n_vizinhos

    @property
    def metrica(self) -> str:
        """Métrica de distância no espaço original."""
        return self._metrica

    def ajustar_e_reduzir(self, matriz: csr_matrix | np.ndarray) -> np.ndarray:
        """Ajusta o redutor UMAP e projeta os vetores com adaptação defensiva de amostras."""
        dados = matriz.toarray() if isinstance(matriz, csr_matrix) else np.asarray(matriz)
        shape = dados.shape
        n_amostras = shape[0] if shape else 0
        n_features = shape[1] if len(shape) > 1 else 0

        # Para conjuntos muito pequenos (ex: menos de 4 comentários), preserva espaço original
        if n_amostras < 4 or n_features < 2:
            return dados

        # Ajusta parâmetros de segurança para evitar exceções em amostras pequenas por vídeo
        n_comp_efetivo = min(self._componentes, max(2, n_amostras - 2))
        n_vizinhos_efetivo = min(self._n_vizinhos, max(2, n_amostras - 1))

        from umap import UMAP

        modelo_umap = UMAP(
            n_components=n_comp_efetivo,
            n_neighbors=n_vizinhos_efetivo,
            min_dist=self._distancia_minima,
            metric=self._metrica,
            random_state=self._random_state,
            transform_seed=self._random_state,
        )

        self._redutor = modelo_umap
        matriz_arr = np.asarray(modelo_umap.fit_transform(dados))

        if self._norma is not None and len(matriz_arr.shape) > 0 and matriz_arr.shape[0] > 0:
            matriz_arr = cast(np.ndarray, normalize(matriz_arr, norm=self._norma))

        return matriz_arr

    def reduzir(self, matriz: csr_matrix | np.ndarray) -> np.ndarray:
        """Projeta novos vetores no espaço já ajustado."""
        dados = matriz.toarray() if isinstance(matriz, csr_matrix) else np.asarray(matriz)
        if self._redutor is None:
            return self.ajustar_e_reduzir(dados)

        transform_func = getattr(self._redutor, "transform", None)
        if callable(transform_func):
            matriz_arr = np.asarray(transform_func(dados))
            if self._norma is not None and len(matriz_arr.shape) > 0 and matriz_arr.shape[0] > 0:
                matriz_arr = cast(np.ndarray, normalize(matriz_arr, norm=self._norma))
            return matriz_arr

        return dados
