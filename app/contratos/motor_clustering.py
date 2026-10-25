"""Contratos para algoritmos e motores de clustering."""

from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class ProtocoloMotorClustering(Protocol):
    """Protocolo abstrato para algoritmos de clustering (KMeans, DBSCAN, HDBSCAN)."""

    def ajustar(self, matriz_treino: np.ndarray) -> "ProtocoloMotorClustering":
        """Ajusta o algoritmo de clustering à matriz de treino."""
        ...

    def obter_rotulos(self) -> list[int]:
        """Retorna os rótulos de cluster atribuídos a cada amostra (-1 indica ruído)."""
        ...

    @property
    def tem_centroides(self) -> bool:
        """Indica se o algoritmo possui centroides matematicamente definidos."""
        ...

    def obter_centroides(self) -> np.ndarray | None:
        """Retorna as coordenadas dos centroides ou None se não aplicável."""
        ...

    @property
    def suporta_previsao(self) -> bool:
        """Indica se o algoritmo pode predizer clusters para novos pontos out-of-sample."""
        ...

    def prever(self, matriz_amostras: np.ndarray) -> list[int]:
        """Prediz os clusters para novas amostras caso suportado."""
        ...
