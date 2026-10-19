"""Higienização de texto para processamento de linguagem natural."""

import re


class LimpadorTexto:
    """Aplica regras de higienização de texto preservando o conteúdo original intacto."""

    _PADRAO_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
    _PADRAO_MENCAO = re.compile(r"@[\w.-]+")
    _PADRAO_PONTUACAO_EXCESSIVA = re.compile(r"[!?.]{2,}")
    _PADRAO_ESPACOS = re.compile(r"\s+")

    @classmethod
    def normalizar(cls, texto: str) -> str:
        """Limpa URLs, menções e normaliza espaços sem alterar o sentido do comentário."""
        if not texto.strip():
            return ""

        sem_url = cls._PADRAO_URL.sub(" ", texto)
        sem_mencao = cls._PADRAO_MENCAO.sub(" ", sem_url)
        sem_pontuacao = cls._PADRAO_PONTUACAO_EXCESSIVA.sub(" ", sem_mencao)
        limpo = cls._PADRAO_ESPACOS.sub(" ", sem_pontuacao).strip()
        return limpo
