"""Tokenização, POS tagging e lematização em língua portuguesa via spaCy."""

import spacy
from spacy.language import Language


class LematizadorSpacy:
    """Encapsula o pipeline spaCy para extração de lemas com controle de negações e stopwords."""

    def __init__(
        self,
        modelo_nome: str = "pt_core_news_sm",
        stopwords_adicionais: list[str] | None = None,
        preservar_negacoes: list[str] | None = None,
        pos_permitidas: list[str] | None = None,
    ) -> None:
        self._modelo_nome: str = modelo_nome
        self._nlp: Language = spacy.load(modelo_nome)

        # Configura negações preservadas (não devem ser removidas como stopword)
        self._preservar: set[str] = set(preservar_negacoes or ["nao", "não", "nunca", "sem", "jamais"])
        for termo in self._preservar:
            if termo in self._nlp.vocab:
                self._nlp.vocab[termo].is_stop = False

        # Configura stopwords adicionais
        self._adicionais: set[str] = set(stopwords_adicionais or [])
        for termo in self._adicionais:
            if termo in self._nlp.vocab and termo not in self._preservar:
                self._nlp.vocab[termo].is_stop = True

        self._pos_permitidas: set[str] = set(pos_permitidas or ["NOUN", "PROPN", "ADJ"])

    def processar_texto(self, texto: str) -> list[str]:
        """Extrai lemas filtrados por tamanho e classe gramatical."""
        if not texto.strip():
            return []

        doc = self._nlp(texto.lower())
        lemas: list[str] = []

        for token in doc:
            lema = token.lemma_.strip()
            texto_token = token.text.strip()

            if not lema or len(lema) < 3:
                continue

            # Preserva negação se configurada
            if texto_token in self._preservar or lema in self._preservar:
                lemas.append(lema)
                continue

            if token.is_stop or token.is_punct or token.is_space or token.like_url:
                continue

            if token.pos_ in self._pos_permitidas:
                lemas.append(lema)

        return lemas

    def extrair_candidatos_topico(self, texto: str) -> list[tuple[str, str]]:
        """Retorna tuplas (lema, pos) dos candidatos a tópico."""
        if not texto.strip():
            return []

        doc = self._nlp(texto.lower())
        candidatos: list[tuple[str, str]] = []

        for token in doc:
            lema = token.lemma_.strip()
            texto_token = token.text.strip()

            if len(lema) < 3 or token.is_punct or token.is_space:
                continue

            if token.is_stop and texto_token not in self._preservar:
                continue

            if token.pos_ in self._pos_permitidas:
                candidatos.append((lema, token.pos_))

        return candidatos
