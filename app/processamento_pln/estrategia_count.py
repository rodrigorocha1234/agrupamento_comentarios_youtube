"""Estratégia concreta de vetorização de texto usando CountVectorizer (GoF Concrete Strategy)."""

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

from app.conf_yaml import ConfigCountInfo


class EstrategiaTratamentoCount:
    """Vetoriza textos através de contagem de frequência de termos (Bag of Words)."""

    def __init__(self, config: ConfigCountInfo | None = None) -> None:
        self._config = config or ConfigCountInfo()
        ngram_min = self._config.ngram_range[0] if self._config.ngram_range else 1
        ngram_max = self._config.ngram_range[1] if len(self._config.ngram_range) > 1 else ngram_min
        self._vectorizer = CountVectorizer(
            max_features=self._config.max_features,
            ngram_range=(ngram_min, ngram_max),
            min_df=self._config.min_df,
        )

    def processar_textos(self, textos: Sequence[str]) -> pd.DataFrame:
        """Ajusta e transforma os textos em contagens convertidas para DataFrame."""
        textos_limpos = [str(t or "").strip() or "sem_comentario" for t in textos]
        if not textos_limpos:
            return pd.DataFrame()

        matriz_esparsa = self._vectorizer.fit_transform(textos_limpos)
        toarray_func = getattr(matriz_esparsa, "toarray", None)
        matriz_array = toarray_func() if callable(toarray_func) else np.asarray(matriz_esparsa)
        nomes_features = [f"count_{n}" for n in self._vectorizer.get_feature_names_out()]
        return pd.DataFrame(np.asarray(matriz_array, dtype=np.float64), columns=nomes_features)
