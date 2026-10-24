"""Adaptador scikit-learn para algoritmo DBSCAN baseado em densidade e ruído."""

from typing import final, override

import numpy as np
from sklearn.cluster import DBSCAN

from app.agrupamento_modelos.capacidades_algoritmo import (
    CapacidadesAlgoritmo,
    EstrategiaAgrupamento,
)


@final
class AgrupadorDbscan(EstrategiaAgrupamento):
    """Adaptador de DBSCAN: sem centroides, sem predição fora da amostra e com ruído (-1)."""

    def __init__(self, eps: float = 0.5, min_samples: int = 5) -> None:
        self._modelo = DBSCAN(eps=eps, min_samples=min_samples)
        self._capacidades = CapacidadesAlgoritmo(
            nome_algoritmo="dbscan",
            suporta_predicao_fora_da_amostra=False,
            possui_centroides=False,
            gera_ruido=True,
            rotulo_ruido=-1,
        )

    @property
    @override
    def capacidades(self) -> CapacidadesAlgoritmo:
        return self._capacidades

    @override
    def treinar(self, matriz_x: np.ndarray) -> np.ndarray:
        rotulos = self._modelo.fit_predict(matriz_x)
        return np.asarray(rotulos, dtype=np.int32)

    @override
    def predizer(self, matriz_x: np.ndarray) -> np.ndarray:
        raise NotImplementedError(
            "O algoritmo DBSCAN opera por densidade local e não oferece predição indutiva fora da amostra."
        )

    @override
    def obter_centroides(self) -> np.ndarray | None:
        return None
