"""Estratégia concreta de tratamento de texto usando spaCy (GoF Concrete Strategy)."""

from collections.abc import Sequence
from typing import Final

import numpy as np
import pandas as pd
import spacy
from spacy.language import Language

from app.conf_yaml import ConfigSpacyInfo
from app.excecoes import ErroPreprocessamento

_CACHE_MODELOS: Final[dict[str, Language]] = {}


class EstrategiaTratamentoSpacy:
    """Extrai representações vetoriais densas (embeddings) via modelo de linguagem spaCy."""

    def __init__(self, config: ConfigSpacyInfo | None = None) -> None:
        self._config = config or ConfigSpacyInfo()
        self._nlp = self._obter_pipeline_spacy(self._config.modelo)

    @classmethod
    def _obter_pipeline_spacy(cls, nome_modelo: str) -> Language:
        if nome_modelo not in _CACHE_MODELOS:
            try:
                _CACHE_MODELOS[nome_modelo] = spacy.load(nome_modelo)
            except Exception as exc:
                raise ErroPreprocessamento(
                    f"Falha ao carregar modelo spaCy '{nome_modelo}': {exc}. "
                    "Certifique-se de que o modelo foi instalado (ex: python -m spacy download pt_core_news_sm)."
                ) from exc
        return _CACHE_MODELOS[nome_modelo]

    def processar_textos(self, textos: Sequence[str]) -> pd.DataFrame:
        """Limpa e gera matriz de embeddings semânticos dos textos com spaCy."""
        if not textos:
            return pd.DataFrame()

        # Determina a dimensão vetorial do modelo (ex: 96 para sm, 300 para lg)
        dimensao_vetor: int = self._nlp.vocab.vectors_length or 96

        vetores: list[np.ndarray] = []
        for texto in textos:
            texto_limpo = str(texto or "").strip()
            if self._config.converter_minusculas:
                texto_limpo = texto_limpo.lower()

            doc = self._nlp(texto_limpo)

            tokens_validos = [
                token.lemma_ if self._config.lematizar else token.text
                for token in doc
                if (not self._config.remover_stopwords or not token.is_stop)
                and (not self._config.remover_pontuacao or not token.is_punct)
                and (not self._config.remover_numeros or not token.is_digit)
                and not token.is_space
            ]

            if tokens_validos:
                doc_filtrado = self._nlp(" ".join(tokens_validos))
                vetor = np.asarray(doc_filtrado.vector, dtype=np.float64)
                if vetor.shape[0] == 0:
                    vetor = np.zeros(dimensao_vetor, dtype=np.float64)
                elif vetor.shape[0] != dimensao_vetor:
                    dimensao_vetor = vetor.shape[0]
                vetores.append(vetor)
            else:
                vetores.append(np.zeros(dimensao_vetor, dtype=np.float64))

        matriz = np.vstack(vetores).astype(np.float64)
        qtd_dims = matriz.shape[1]
        colunas = [f"spacy_emb_{i}" for i in range(qtd_dims)]
        return pd.DataFrame(matriz, columns=colunas)
