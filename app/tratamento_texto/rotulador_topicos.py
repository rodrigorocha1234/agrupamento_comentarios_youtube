"""Rotulador determinístico de tópicos não-LLM baseado em lemas e relevância estatística."""

from collections import Counter
import math


class RotuladorTopicos:
    """Calcula o melhor lema representativo (exatamente uma palavra) para um grupo de textos."""

    def __init__(
        self,
        peso_tfidf: float = 0.7,
        peso_frequencia: float = 0.3,
        penalizacao_global: bool = True,
        comprimento_minimo: int = 3,
        limiar_penalizacao_global: float = 0.75,
        fator_penalidade: float = 0.2,
        rotulo_ruido_padrao: str = "sem_topico",
    ) -> None:
        self._peso_tfidf: float = peso_tfidf
        self._peso_frequencia: float = peso_frequencia
        self._penalizacao_global: bool = penalizacao_global
        self._comprimento_minimo: int = max(2, comprimento_minimo)
        self._limiar_penalizacao_global: float = limiar_penalizacao_global
        self._fator_penalidade: float = fator_penalidade
        self._rotulo_ruido_padrao: str = rotulo_ruido_padrao

    def rotular_cluster(
        self,
        lemas_cluster: list[list[str]],
        lemas_globais: list[list[str]],
    ) -> str:
        """Determina o lema de maior pontuação para o cluster ou retorna o rótulo de ruído padrão."""
        if not lemas_cluster:
            return self._rotulo_ruido_padrao

        todos_cluster = [
            lema for sublista in lemas_cluster for lema in sublista if len(lema) >= self._comprimento_minimo
        ]
        if not todos_cluster:
            return self._rotulo_ruido_padrao

        contagem_cluster = Counter(todos_cluster)
        total_termos_cluster = len(todos_cluster)

        # Contagem em todos os documentos (frequência de documentos)
        total_docs_globais = max(1, len(lemas_globais))
        freq_docs: Counter[str] = Counter()
        for doc in lemas_globais:
            termos_unicos = set(doc)
            for t in termos_unicos:
                freq_docs[t] += 1

        melhor_lema: str = self._rotulo_ruido_padrao
        maior_pontuacao: float = -1.0

        for lema, freq in contagem_cluster.items():
            # TF normalizado
            tf = freq / total_termos_cluster
            # IDF inverso
            df = freq_docs.get(lema, 1)
            idf = math.log((total_docs_globais + 1) / (df + 1)) + 1.0
            tfidf = tf * idf

            # Frequência relativa dentro do cluster
            freq_relativa = freq / total_termos_cluster

            # Penalização se o termo aparece acima do limiar em todos os documentos
            penalidade = 1.0
            if self._penalizacao_global and (df / total_docs_globais) > self._limiar_penalizacao_global:
                penalidade = self._fator_penalidade

            score = (
                (self._peso_tfidf * tfidf) + (self._peso_frequencia * freq_relativa)
            ) * penalidade

            if score > maior_pontuacao:
                maior_pontuacao = score
                melhor_lema = lema

        return melhor_lema if melhor_lema != "" else self._rotulo_ruido_padrao
