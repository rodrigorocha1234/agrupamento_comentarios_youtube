"""Representação vetorial de textos utilizando TF-IDF."""

from typing import cast
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer


class VetorizadorTfidf:
    """Aplica vetorização TF-IDF sobre textos lematizados com parâmetros configuráveis."""

    def __init__(
        self,
        min_df: int = 2,
        max_df: float = 0.95,
        ngram_range: tuple[int, int] = (1, 2),
        sublinear_tf: bool = True,
        norma: str = "l2",
    ) -> None:
        self._vetorizador = TfidfVectorizer(
            min_df=min_df,
            max_df=max_df,
            ngram_range=ngram_range,
            sublinear_tf=sublinear_tf,
            norm=norma,
        )
        self._ajustado: bool = False

    def ajustar_e_transformar(self, textos: list[str]) -> csr_matrix:
        """Ajusta o vocabulário e projeta os textos no espaço vetorial TF-IDF."""
        if not textos:
            return csr_matrix((0, 0), dtype=np.float64)

        try:
            matriz = self._vetorizador.fit_transform(textos)
        except ValueError:
            self._vetorizador.set_params(min_df=1, max_df=1.0)
            matriz = self._vetorizador.fit_transform(textos)

        self._ajustado = True
        return cast(csr_matrix, matriz)

    def transformar(self, textos: list[str]) -> csr_matrix:
        """Projeta novos textos no espaço vetorial já ajustado."""
        if not self._ajustado or not textos:
            return csr_matrix((len(textos), 0), dtype=np.float64)
        matriz = self._vetorizador.transform(textos)
        return cast(csr_matrix, matriz)

    def obter_nomes_caracteristicas(self) -> list[str]:
        """Retorna os termos que compõem o vocabulário ajustado."""
        if not self._ajustado:
            return []
        termos = self._vetorizador.get_feature_names_out()
        return list(cast(list[str], termos))
