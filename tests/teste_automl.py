"""Testes automatizados para a seleção automatizada de modelos (AutoML)."""

import numpy as np
from sklearn.datasets import make_blobs

from app.agrupamento_modelos.selecionador_automl import SelecionadorModelosAutoML


def teste_selecao_automl_eleicao_campeao() -> None:
    """Valida a execução de AutoML avaliando múltiplos algoritmos e elegendo o ótimo."""
    retorno_blobs = make_blobs(
        n_samples=150,
        centers=3,
        n_features=2,
        cluster_std=0.5,
        random_state=42,
    )
    matriz_x = np.asarray(retorno_blobs[0], dtype=np.float64)


    selecionador = SelecionadorModelosAutoML()
    candidatos = [
        ("kmeans", {"n_clusters": 2, "n_init": 10}),
        ("kmeans", {"n_clusters": 3, "n_init": 10}),
        ("kmeans", {"n_clusters": 5, "n_init": 10}),
    ]

    modelo, avaliacao, nome_algoritmo, score = selecionador.selecionar_melhor_modelo(
        matriz_x, candidatos=candidatos
    )

    assert modelo is not None
    assert avaliacao.total_clusters in (2, 3)
    assert nome_algoritmo == "kmeans"

    assert score > 0.5
