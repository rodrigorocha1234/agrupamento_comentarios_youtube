import numpy as np
import pytest
from sklearn.datasets import make_blobs

from app.otimizacao_hiperparametros.avaliador_objetivo import AvaliadorObjetivo
from app.otimizacao_hiperparametros.buscador_parametros import BuscadorParametros


def teste_otimizacao_kmeans_eleicao_campeao() -> None:
    """Valida a busca em grade de k para KMeans elegendo o k com maior separação."""
    # Gera 3 clusters bem definidos
    retorno_blobs = make_blobs(n_samples=120, n_features=3, centers=3, random_state=42)
    x_dados = np.asarray(retorno_blobs[0], dtype=np.float64)

    buscador = BuscadorParametros()
    grade = [
        {"n_clusters": 2, "random_state": 42},
        {"n_clusters": 3, "random_state": 42},
        {"n_clusters": 5, "random_state": 42},
    ]

    resultado = buscador.otimizar("kmeans", x_dados, grade)

    assert resultado.melhor_modelo is not None
    assert len(resultado.historico_tentativas) == 3
    # Garante que o modelo campeão foi eleito com excelente separação
    assert resultado.melhores_parametros.get("n_clusters") in [2, 3]
    assert (resultado.melhores_metricas.silhouette_global or 0.0) > 0.7
    assert resultado.score_campeao > 0.7


def teste_avaliador_objetivo_penaliza_cluster_unico() -> None:
    """Garante que soluções triviais ou de ruído total sejam desqualificadas."""
    from app.avaliacao_modelos.metricas_estatisticas import ResultadoAvaliacao

    avaliador = AvaliadorObjetivo()
    metricas_invalidas = ResultadoAvaliacao(
        total_amostras=100,
        total_clusters=1,
        total_ruido=0,
        proporcao_ruido=0.0,
        silhouette_global=-1.0,
        silhouette_sem_ruido=None,
        davies_bouldin=None,
        calinski_harabasz=None,
        tamanhos_clusters={0: 100},
    )

    res = avaliador.calcular_score(metricas_invalidas)
    assert not res.valido
    assert res.score_composto == -1.0


def teste_buscador_rejeita_grade_vazia() -> None:
    """Verifica lançamento de erro quando grade de parâmetros for vazia."""
    retorno_blobs = make_blobs(n_samples=20, n_features=2, centers=2, random_state=42)
    x_dados = np.asarray(retorno_blobs[0], dtype=np.float64)
    buscador = BuscadorParametros()

    with pytest.raises(ValueError, match="não pode estar vazia"):
        buscador.otimizar("kmeans", x_dados, [])
