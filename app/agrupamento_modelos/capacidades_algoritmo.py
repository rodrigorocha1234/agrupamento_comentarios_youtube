"""Catálogo tipado de capacidades para algoritmos de clustering."""

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True, slots=True)
class CapacidadesAlgoritmo:
    """Declaração formal das propriedades operacionais de um algoritmo de agrupamento."""

    nome_algoritmo: str
    suporta_predicao_fora_da_amostra: bool
    possui_centroides: bool
    gera_ruido: bool
    rotulo_ruido: int = -1


class EstrategiaAgrupamento(Protocol):
    """Protocolo comum para algoritmos de clustering scikit-learn."""

    @property
    def capacidades(self) -> CapacidadesAlgoritmo:
        """Propriedades e limitações operacionais do algoritmo."""
        ...

    def treinar(self, matriz_x: np.ndarray) -> np.ndarray:
        """Ajusta o algoritmo e retorna o vetor de rótulos de cluster."""
        ...

    def predizer(self, matriz_x: np.ndarray) -> np.ndarray:
        """Atribui clusters para novos registros se suportado pelas capacidades."""
        ...

    def obter_centroides(self) -> np.ndarray | None:
        """Retorna coordenadas dos centroides ou None se o algoritmo não possuir centroides."""
        ...
