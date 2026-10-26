"""Estratégia concreta de vetorização de texto usando TF-IDF (GoF Concrete Strategy)."""

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from app.conf_yaml import ConfigTFIDFInfo


class EstrategiaTratamentoTFIDF:
    """Vetoriza textos usando o algoritmo Term Frequency-Inverse Document Frequency (TF-IDF)."""

    def __init__(self, config: ConfigTFIDFInfo | None = None) -> None:
        self._config = config or ConfigTFIDFInfo()
        ngram_min = self._config.ngram_range[0] if self._config.ngram_range else 1
        ngram_max = self._config.ngram_range[1] if len(self._config.ngram_range) > 1 else ngram_min
        self._vectorizer = TfidfVectorizer(
            max_features=self._config.max_features,
            ngram_range=(ngram_min, ngram_max),
            min_df=self._config.min_df,
            max_df=self._config.max_df,
            sublinear_tf=self._config.sublinear_tf,
        )

    def processar_textos(self, textos: Sequence[str]) -> pd.DataFrame:
        """Ajusta e transforma os textos em matriz esparsa convertida para DataFrame."""
        textos_limpos = [str(t or "").strip() or "sem_comentario" for t in textos]
        if not textos_limpos:
            return pd.DataFrame()

        matriz_esparsa = self._vectorizer.fit_transform(textos_limpos)
        nomes_features = [f"tfidf_{n}" for n in self._vectorizer.get_feature_names_out()]
        return pd.DataFrame(matriz_esparsa.toarray().astype(np.float64), columns=nomes_features)
