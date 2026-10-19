"""Representação vetorial semântica densa baseada em embeddings do spaCy com normalização L2."""

from typing import cast
import numpy as np
import spacy
from spacy.language import Language



class ExtratorEmbeddings:
    """Extrai vetores densos normalizados a partir do modelo spaCy com agregação e fallback."""

    def __init__(
        self,
        modelo_nome: str = "pt_core_news_sm",
        nlp_existente: Language | None = None,
        norma: str = "l2",
    ) -> None:
        self._norma: str = norma
        if nlp_existente is not None:
            self._nlp: Language = nlp_existente
        else:
            self._nlp = spacy.load(modelo_nome)

    def extrair_vetores(self, textos: list[str]) -> np.ndarray:
        """Gera matriz densa (N x D) de embeddings normalizados em L2."""
        if not textos:
            return np.empty((0, 0), dtype=np.float64)

        vetores_lista: list[np.ndarray] = []
        dimensao_padrao: int = 0

        for texto in textos:
            texto_limpo = texto.strip()
            if not texto_limpo:
                vetores_lista.append(np.array([], dtype=np.float64))
                continue

            doc = self._nlp(texto_limpo)
            # Extrai o vetor denso do documento gerado pelo modelo spaCy
            vetor = cast(np.ndarray, doc.vector)
            if vetor.ndim == 1 and vetor.shape[0] > 0:
                dimensao_padrao = max(dimensao_padrao, vetor.shape[0])
                vetores_lista.append(vetor.astype(np.float64))
            else:
                vetores_lista.append(np.array([], dtype=np.float64))

        if dimensao_padrao == 0:
            dimensao_padrao = 96

        matriz = np.zeros((len(textos), dimensao_padrao), dtype=np.float64)
        for i, v in enumerate(vetores_lista):
            if v.size == dimensao_padrao:
                matriz[i] = v
            elif v.size > 0:
                limite = min(v.size, dimensao_padrao)
                matriz[i, :limite] = v[:limite]
            else:
                matriz[i] = np.zeros(dimensao_padrao, dtype=np.float64)

        # Normaliza L2 para garantir que distâncias Euclidianas reflitam distância de Cosseno
        if self._norma:
            normas = np.linalg.norm(matriz, axis=1, keepdims=True)
            normas[normas == 0.0] = 1.0
            matriz = matriz / normas

        return matriz
