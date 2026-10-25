"""Controlador de resiliência, backoff exponencial, jitter e tratamento de HTTP 429."""

import random
import time
from typing import final


class ErroRequisicaoEsgotada(Exception):
    """Exceção levantada quando o número máximo de tentativas de requisição for excedido."""


@final
class ControladorResiliencia:
    """Aplica estratégias de retry com backoff exponencial e espera por rate limit."""

    def __init__(
        self,
        max_tentativas: int = 5,
        espera_base_segundos: float = 1.0,
        espera_429_segundos: float = 30.0,
    ) -> None:
        self._max_tentativas = max_tentativas
        self._espera_base = espera_base_segundos
        self._espera_429 = espera_429_segundos

    def calcular_espera_backoff(self, tentativa: int) -> float:
        """Calcula o tempo de espera com backoff exponencial e jitter aleatório proporcional."""
        fator = 2 ** (tentativa - 1)
        jitter = random.uniform(0.0, 0.1 * self._espera_base)
        return float((self._espera_base * fator) + jitter)

    def esperar_por_taxa_limite(self) -> None:
        """Pausa o fluxo em caso de resposta HTTP 429 (Too Many Requests)."""
        time.sleep(self._espera_429)

    def executar_pausa_tentativa(self, tentativa: int) -> None:
        """Pausa o fluxo conforme o cálculo de backoff."""
        if tentativa >= self._max_tentativas:
            raise ErroRequisicaoEsgotada(
                f"Limite de {self._max_tentativas} tentativas de requisição foi esgotado."
            )
        tempo = self.calcular_espera_backoff(tentativa)
        time.sleep(tempo)
