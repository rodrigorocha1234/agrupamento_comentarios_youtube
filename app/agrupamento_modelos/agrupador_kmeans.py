"""Estratégia de agrupamento utilizando o algoritmo KMeans com otimização automática de clusters."""

from typing import cast
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans

from app.agrupamento_modelos.avaliador_qualidade import (
    AvaliadorQualidade,
    MetricasAgrupamento,
)


class AgrupadorKMeans:
    """Implementa clusterização particional via KMeans com seleção automática de k ótimo."""

    def __init__(
        self,
        n_clusters: int = 8,
        random_state: int = 42,
        n_init: int = 10,
        init: str = "k-means++",
        k_automatico: bool = True,
        k_min: int = 2,
        k_max: int = 10,
        max_iter: int = 300,
    ) -> None:
        self._n_clusters_desejado: int = max(1, n_clusters)
        self._random_state: int = random_state
        self._n_init: int = n_init
        self._init: str = str(init)
        self._k_automatico: bool = k_automatico
        self._k_min: int = max(2, k_min)
        self._k_max: int = max(self._k_min, k_max)
        self._max_iter: int = max(1, max_iter)
        self._modelo: KMeans | None = None
        self._k_otimo: int = self._n_clusters_desejado
        self._historico_k: dict[int, float] = {}
        self._rotulos: list[int] = []

    def ajustar_e_agrupar(
        self,
        matriz: csr_matrix | np.ndarray,
    ) -> tuple[list[int], MetricasAgrupamento]:
        """Ajusta o KMeans aos dados (otimizando k ou usando valor fixo) e retorna rótulos e métricas."""
        n_amostras = matriz.shape[0] if matriz.shape else 0
        if n_amostras == 0:
            self._rotulos = []
            return [], AvaliadorQualidade.avaliar(matriz, [])

        if self._k_automatico and n_amostras >= 3:
            rotulos, metricas = self._executar_busca_k_otimo(matriz, n_amostras)
            self._rotulos = rotulos
            return rotulos, metricas

        k_efetivo = max(1, min(self._n_clusters_desejado, n_amostras))
        self._k_otimo = k_efetivo
        self._modelo = KMeans(
            n_clusters=k_efetivo,
            init=self._init,
            random_state=self._random_state,
            n_init=cast(str, self._n_init),
            max_iter=self._max_iter,
        )

        rotulos_arr = self._modelo.fit_predict(matriz)
        rotulos_lista = [int(r) for r in rotulos_arr]
        metricas = AvaliadorQualidade.avaliar(matriz, rotulos_arr)
        if metricas.pontuacao_silhueta is not None:
            self._historico_k = {k_efetivo: metricas.pontuacao_silhueta}
        self._rotulos = rotulos_lista
        return rotulos_lista, metricas


    def _executar_busca_k_otimo(
        self,
        matriz: csr_matrix | np.ndarray,
        n_amostras: int,
    ) -> tuple[list[int], MetricasAgrupamento]:
        """Varre o intervalo [k_min, k_max] selecionando o k com maior pontuação de silhueta."""
        limite_superior = min(self._k_max, n_amostras - 1)
        if limite_superior < self._k_min:
            k_fallback = max(1, min(self._k_min, n_amostras))
            self._k_otimo = k_fallback
            self._modelo = KMeans(
                n_clusters=k_fallback,
                init=self._init,
                random_state=self._random_state,
                n_init=cast(str, self._n_init),
                max_iter=self._max_iter,
            )
            rotulos_arr = self._modelo.fit_predict(matriz)
            return [int(r) for r in rotulos_arr], AvaliadorQualidade.avaliar(matriz, rotulos_arr)

        melhor_k = self._k_min
        melhor_score = -2.0
        melhor_modelo: KMeans | None = None
        melhor_rotulos: np.ndarray | None = None
        melhores_metricas: MetricasAgrupamento | None = None
        self._historico_k = {}

        for k in range(self._k_min, limite_superior + 1):
            cand_modelo = KMeans(
                n_clusters=k,
                init=self._init,
                random_state=self._random_state,
                n_init=cast(str, self._n_init),
                max_iter=self._max_iter,
            )
            rotulos_cand = cand_modelo.fit_predict(matriz)
            n_rotulos_unicos = len(set(rotulos_cand))
            if n_rotulos_unicos <= 1 or n_rotulos_unicos >= n_amostras:
                continue

            metricas_cand = AvaliadorQualidade.avaliar(matriz, rotulos_cand)
            score = (
                metricas_cand.pontuacao_silhueta
                if metricas_cand.pontuacao_silhueta is not None
                else -1.0
            )
            self._historico_k[k] = score

            if score > melhor_score or melhor_modelo is None:
                melhor_score = score
                melhor_k = k
                melhor_modelo = cand_modelo
                melhor_rotulos = rotulos_cand
                melhores_metricas = metricas_cand

        if melhor_modelo is None or melhor_rotulos is None or melhores_metricas is None:
            k_fallback = max(1, min(self._k_min, n_amostras))
            self._k_otimo = k_fallback
            self._modelo = KMeans(
                n_clusters=k_fallback,
                init=self._init,
                random_state=self._random_state,
                n_init=cast(str, self._n_init),
                max_iter=self._max_iter,
            )
            rotulos_arr = self._modelo.fit_predict(matriz)
            return [int(r) for r in rotulos_arr], AvaliadorQualidade.avaliar(matriz, rotulos_arr)

        self._k_otimo = melhor_k
        self._modelo = melhor_modelo
        rotulos_lista = [int(r) for r in melhor_rotulos]
        return rotulos_lista, melhores_metricas

    def obter_init(self) -> str:
        """Retorna a estratégia de inicialização dos centróides (ex: 'k-means++')."""
        return self._init

    def obter_centroides(self) -> np.ndarray | None:
        """Retorna as coordenadas dos centros dos clusters após o ajuste."""
        if self._modelo is None or not hasattr(self._modelo, "cluster_centers_"):
            return None
        return cast(np.ndarray, self._modelo.cluster_centers_)

    def obter_modelo(self) -> KMeans | None:
        """Retorna a instância do modelo scikit-learn treinado para registro no MLflow."""
        return self._modelo

    def obter_k_otimo(self) -> int:
        """Retorna o número ótimo de clusters selecionado durante o ajuste."""
        return self._k_otimo

    def obter_historico_k(self) -> dict[int, float]:
        """Retorna a pontuação de silhueta calculada para cada k testado na busca."""
        return dict(self._historico_k)

    def obter_rotulos(self) -> list[int]:
        """Retorna os rótulos (labels) de cluster atribuídos a cada amostra ajustada."""
        return list(self._rotulos)

    @property
    def labels_(self) -> np.ndarray:
        """Propriedade padrão compatível com Scikit-Learn que retorna o array de rótulos (labels_)."""
        if self._modelo is not None and hasattr(self._modelo, "labels_"):
            return cast(np.ndarray, self._modelo.labels_)
        return np.array(self._rotulos, dtype=int)

