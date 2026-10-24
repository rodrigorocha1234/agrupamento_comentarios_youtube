from collections.abc import Callable
from typing import Literal, cast, final, override

import numpy as np
from sklearn.cluster import KMeans

from app.agrupamento_modelos.capacidades_algoritmo import (
    CapacidadesAlgoritmo,
    EstrategiaAgrupamento,
)

TipoKMeansConstrutor = Callable[..., KMeans]


@final
class AgrupadorKMeans(EstrategiaAgrupamento):
    """Adaptador de KMeans com capacidades de centroides e atribuição fora da amostra."""

    def __init__(
        self,
        n_clusters: int = 4,
        random_state: int = 42,
        n_init: int | Literal["auto"] = 10,
    ) -> None:
        self._n_clusters = n_clusters
        criador = cast(TipoKMeansConstrutor, KMeans)
        self._modelo = criador(
            n_clusters=n_clusters,
            random_state=random_state,
            n_init=n_init,
        )
        self._capacidades = CapacidadesAlgoritmo(
            nome_algoritmo="kmeans",
            suporta_predicao_fora_da_amostra=True,
            possui_centroides=True,
            gera_ruido=False,
            rotulo_ruido=-1,
        )
        self._ajustado = False

    @property
    @override
    def capacidades(self) -> CapacidadesAlgoritmo:
        return self._capacidades

    @override
    def treinar(self, matriz_x: np.ndarray) -> np.ndarray:
        rotulos = self._modelo.fit_predict(matriz_x)
        self._ajustado = True
        return np.asarray(rotulos, dtype=np.int32)

    @override
    def predizer(self, matriz_x: np.ndarray) -> np.ndarray:
        if not self._ajustado:
            raise RuntimeError(
                "O modelo KMeans deve ser treinado antes de realizar predições."
            )
        rotulos = self._modelo.predict(matriz_x)
        return np.asarray(rotulos, dtype=np.int32)

    @override
    def obter_centroides(self) -> np.ndarray | None:
        if not self._ajustado:
            return None
        return np.asarray(self._modelo.cluster_centers_, dtype=np.float64)
