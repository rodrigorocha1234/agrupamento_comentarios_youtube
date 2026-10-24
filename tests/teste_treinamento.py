"""Teste de integração para o orquestrador de treinamento e geração de dados Gold."""

import numpy as np
import pandas as pd

from app.configuracao_geral.conf_yaml import ConfYAML
from app.treinamento_pipeline.executor_treinamento import ExecutorTreinamento


def teste_ciclo_treinamento_kmeans_gold() -> None:
    """Executa o pipeline completo da Fase 2 gerando dataset Gold e relatório estatístico."""
    conf = ConfYAML()
    executor = ExecutorTreinamento(configuracoes=conf)

    # Simulação de dataset Silver normalizado
    rng = np.random.default_rng(42)
    n = 50

    # Grupo 1: Jogadores novatos / pouco tempo
    c1_forever = rng.uniform(60.0, 300.0, size=n // 2)
    c1_review = rng.uniform(30.0, 150.0, size=n // 2)
    c1_recent = rng.uniform(0.0, 30.0, size=n // 2)

    # Grupo 2: Veteranos / muito tempo
    c2_forever = rng.uniform(5000.0, 15000.0, size=n // 2)
    c2_review = rng.uniform(3000.0, 10000.0, size=n // 2)
    c2_recent = rng.uniform(500.0, 2000.0, size=n // 2)

    df_silver = pd.DataFrame(
        {
            "appid": [427520] * n,
            "recommendationid": [f"REC_{i:04d}" for i in range(n)],
            "steamid": [f"STEAM_{i:04d}" for i in range(n)],
            "language": ["brazilian"] * n,
            "review_texto": [f"Review textual humana {i}" for i in range(n)],
            "timestamp_created": [1690000000 + i * 1000 for i in range(n)],
            "timestamp_updated": [1690000000 + i * 1000 for i in range(n)],
            "voted_up": [True] * n,
            "votes_up": [i % 10 for i in range(n)],
            "comment_count": [0] * n,
            "playtime_forever": np.concatenate([c1_forever, c2_forever]),
            "playtime_last_two_weeks": np.concatenate([c1_recent, c2_recent]),
            "playtime_at_review": np.concatenate([c1_review, c2_review]),
            "last_played": [1700000000 - i * 500 for i in range(n)],
            "num_games_owned": [10 + (i % 20) for i in range(n)],
            "num_reviews": [1 + (i % 5) for i in range(n)],
        }
    )

    dados_gold, avaliacao, agrupador = executor.executar_treinamento(
        dados_silver=df_silver,
        nome_algoritmo="kmeans",
        parametros_algoritmo={"n_clusters": 2, "random_state": 42},
    )

    # Validações no dataset Gold
    assert "cluster_label" in dados_gold.columns
    assert set(dados_gold["cluster_label"]) == {0, 1}
    assert "horas_ate_review" in dados_gold.columns
    assert "dias_desde_ultima_atividade" in dados_gold.columns
    assert len(dados_gold) == n

    # Validações estatísticas
    assert avaliacao.total_clusters == 2
    assert avaliacao.total_amostras == n
    assert avaliacao.total_ruido == 0
    assert avaliacao.silhouette_global is not None
    assert avaliacao.silhouette_global > 0.5

    # Validações de capacidade do algoritmo
    assert agrupador.capacidades.nome_algoritmo == "kmeans"
    assert agrupador.capacidades.possui_centroides is True
