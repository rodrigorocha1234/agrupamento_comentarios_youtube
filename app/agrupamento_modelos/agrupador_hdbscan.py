from collections.abc import Callable
from typing import cast, final, override

import numpy as np
from sklearn.cluster import HDBSCAN

from app.agrupamento_modelos.capacidades_algoritmo import (
    CapacidadesAlgoritmo,
    EstrategiaAgrupamento,
)

TipoHdbscanConstrutor = Callable[..., HDBSCAN]


@final
class AgrupadorHdbscan(EstrategiaAgrupamento):
    """Adaptador de HDBSCAN com identificação de ruído e persistência de probabilidades."""

    def __init__(
        self,
        min_cluster_size: int = 20,
        min_samples: int = 5,
    ) -> None:
        self._min_cluster_size = min_cluster_size
        self._min_samples = min_samples
        criador = cast(TipoHdbscanConstrutor, HDBSCAN)
        self._modelo = criador(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            copy=True,
        )
        self._capacidades = CapacidadesAlgoritmo(
            nome_algoritmo="hdbscan",
            suporta_predicao_fora_da_amostra=False,
            possui_centroides=False,
            gera_ruido=True,
            rotulo_ruido=-1,
        )
        self._probabilidades: np.ndarray | None = None

    @property
    @override
    def capacidades(self) -> CapacidadesAlgoritmo:
        return self._capacidades

    @property
    def probabilidades(self) -> np.ndarray | None:
        """Probabilidades de pertinência dos pontos aos clusters calculadas pelo HDBSCAN."""
        return self._probabilidades

    @override
    def treinar(self, matriz_x: np.ndarray) -> np.ndarray:
        rotulos = self._modelo.fit_predict(matriz_x)
        self._probabilidades = np.asarray(self._modelo.probabilities_, dtype=np.float64)
        return np.asarray(rotulos, dtype=np.int32)

    @override
    def predizer(self, matriz_x: np.ndarray) -> np.ndarray:
        raise NotImplementedError(
            "Predição indutiva padrão não está ativada no HDBSCAN desta configuração."
        )

    @override
    def obter_centroides(self) -> np.ndarray | None:
        return None
