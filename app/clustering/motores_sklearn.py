"""Motores de clustering baseados em scikit-learn aderentes ao ProtocoloMotorClustering."""

from typing import override

import numpy as np
from sklearn.cluster import DBSCAN, HDBSCAN, KMeans

from app.conf_yaml import (
    ConfigParametrosDBSCAN,
    ConfigParametrosHDBSCAN,
    ConfigParametrosKMeans,
)
from app.contratos.motor_clustering import ProtocoloMotorClustering
from app.excecoes import ErroAlgoritmoNaoSuportado, ErroClustering


class MotorKMeans(ProtocoloMotorClustering):
    """Estratégia de agrupamento particional KMeans."""

    def __init__(self, parametros: ConfigParametrosKMeans, random_state: int = 42) -> None:
        self._parametros = parametros
        self._random_state = random_state
        n_init_val: str | int = (
            "auto" if str(parametros.n_init).lower() == "auto" else int(parametros.n_init)
        )
        self._modelo = KMeans(
            n_clusters=parametros.n_clusters,
            init=parametros.init,
            n_init=n_init_val,  # type: ignore[arg-type]
            max_iter=parametros.max_iter,
            random_state=random_state,
        )
        self._rotulos: list[int] = []

    @override
    def ajustar(self, matriz_treino: np.ndarray) -> "MotorKMeans":
        if matriz_treino.shape[0] < self._parametros.n_clusters:
            raise ErroClustering(
                f"Número de amostras ({matriz_treino.shape[0]}) é menor do que n_clusters "
                f"({self._parametros.n_clusters}) para o KMeans."
            )
        try:
            self._modelo.fit(matriz_treino)
            labels = self._modelo.labels_
            self._rotulos = [int(r) for r in labels] if labels is not None else []
            return self
        except Exception as exc:
            raise ErroClustering(f"Falha ao ajustar KMeans: {exc}") from exc

    @override
    def obter_rotulos(self) -> list[int]:
        return list(self._rotulos)

    @property
    @override
    def tem_centroides(self) -> bool:
        return True

    @override
    def obter_centroides(self) -> np.ndarray | None:
        if hasattr(self._modelo, "cluster_centers_"):
            return np.asarray(self._modelo.cluster_centers_)
        return None

    @property
    @override
    def suporta_previsao(self) -> bool:
        return True

    @override
    def prever(self, matriz_amostras: np.ndarray) -> list[int]:
        if not hasattr(self._modelo, "cluster_centers_"):
            raise ErroClustering("O modelo KMeans ainda não foi ajustado.")
        predicoes = self._modelo.predict(matriz_amostras)
        return [int(p) for p in predicoes]

    @property
    def modelo_sklearn(self) -> KMeans:
        """Acesso ao estimador subjacente do scikit-learn para registro no MLflow."""
        return self._modelo


class MotorDBSCAN(ProtocoloMotorClustering):
    """Estratégia de agrupamento por densidade DBSCAN."""

    def __init__(self, parametros: ConfigParametrosDBSCAN) -> None:
        self._parametros = parametros
        self._modelo = DBSCAN(
            eps=parametros.eps,
            min_samples=parametros.min_samples,
            metric=parametros.metric,
        )
        self._rotulos: list[int] = []

    @override
    def ajustar(self, matriz_treino: np.ndarray) -> "MotorDBSCAN":
        if matriz_treino.shape[0] == 0:
            raise ErroClustering("Matriz de treino vazia para ajuste do DBSCAN.")
        try:
            self._modelo.fit(matriz_treino)
            labels = self._modelo.labels_
            self._rotulos = [int(r) for r in labels]
            return self
        except Exception as exc:
            raise ErroClustering(f"Falha ao ajustar DBSCAN: {exc}") from exc

    @override
    def obter_rotulos(self) -> list[int]:
        return list(self._rotulos)

    @property
    @override
    def tem_centroides(self) -> bool:
        return False

    @override
    def obter_centroides(self) -> np.ndarray | None:
        return None

    @property
    @override
    def suporta_previsao(self) -> bool:
        return False

    @override
    def prever(self, matriz_amostras: np.ndarray) -> list[int]:
        raise ErroAlgoritmoNaoSuportado(
            "O algoritmo DBSCAN é estritamente transdutivo e não suporta inferência "
            "indutiva out-of-sample (predict)."
        )

    @property
    def modelo_sklearn(self) -> DBSCAN:
        """Acesso ao estimador subjacente do scikit-learn para registro no MLflow."""
        return self._modelo


class MotorHDBSCAN(ProtocoloMotorClustering):
    """Estratégia de agrupamento por densidade hierárquica HDBSCAN nativa do scikit-learn."""

    def __init__(self, parametros: ConfigParametrosHDBSCAN) -> None:
        self._parametros = parametros
        self._modelo = HDBSCAN(
            min_cluster_size=parametros.min_cluster_size,
            min_samples=parametros.min_samples,
            metric=parametros.metric,
        )
        self._rotulos: list[int] = []

    @override
    def ajustar(self, matriz_treino: np.ndarray) -> "MotorHDBSCAN":
        if matriz_treino.shape[0] == 0:
            raise ErroClustering("Matriz de treino vazia para ajuste do HDBSCAN.")
        try:
            self._modelo.fit(matriz_treino)
            labels = self._modelo.labels_
            self._rotulos = [int(r) for r in labels] if labels is not None else []
            return self
        except Exception as exc:
            raise ErroClustering(f"Falha ao ajustar HDBSCAN: {exc}") from exc

    @override
    def obter_rotulos(self) -> list[int]:
        return list(self._rotulos)

    @property
    @override
    def tem_centroides(self) -> bool:
        return False

    @override
    def obter_centroides(self) -> np.ndarray | None:
        return None

    @property
    @override
    def suporta_previsao(self) -> bool:
        return False

    @override
    def prever(self, matriz_amostras: np.ndarray) -> list[int]:
        raise ErroAlgoritmoNaoSuportado(
            "O algoritmo HDBSCAN opera por densidade hierárquica e não suporta inferência direta via prever()."
        )

    @property
    def modelo_sklearn(self) -> HDBSCAN:
        """Acesso ao estimador subjacente do scikit-learn para registro no MLflow."""
        return self._modelo
