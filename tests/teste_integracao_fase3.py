"""Teste de integração ponta a ponta da Fase 3: Treinamento, MLOps, Negócio e Consulta."""

from pathlib import Path

import pandas as pd

from app.configuracao_geral.conf_yaml import ConfYAML
from app.integracao_mlflow.observador_mlflow import ObservadorMlflow
from app.regras_negocio.rotulador_clusters import RotuladorClusters
from app.servico_consulta.recuperador_reviews import RecuperadorReviews
from app.treinamento_pipeline.executor_treinamento import ExecutorTreinamento
from app.visualizacao_dados.gerador_graficos import GeradorGraficos
from app.visualizacao_dados.painel_executivo import PainelExecutivo


def teste_ciclo_completo_fase3_integrado() -> None:
    """Valida o fluxo integrado de MLOps: treinamento, MLflow, rotulagem e consulta textual."""
    caminho_config = Path("configuracoes")
    config = ConfYAML(diretorio_base=caminho_config)

    # 1. Dados Silver simulados com reviews textuais e métricas de engajamento
    dados_silver = pd.DataFrame(
        {
            "appid": [730] * 30,
            "recommendationid": [f"rec_{i}" for i in range(30)],
            "review_texto": [
                f"Review textual legítima para consulta humana {i}" for i in range(30)
            ],
            "voted_up": [True] * 15 + [False] * 15,
            "votes_up": [i * 2 for i in range(30)],
            "votes_funny": [i for i in range(30)],
            "comment_count": [i % 5 for i in range(30)],
            "steam_purchase": [True] * 30,
            "received_for_free": [False] * 30,
            "written_during_early_access": [False] * 30,
            "num_games_owned": [50] * 30,
            "num_reviews": [5 + (i % 3) for i in range(30)],
            "playtime_forever": [1000 + (i * 200) for i in range(30)],
            "playtime_last_two_weeks": [100 + (i * 10) for i in range(30)],
            "playtime_at_review": [800 + (i * 150) for i in range(30)],
            "last_played": [1700000000] * 30,
            "timestamp_created": [1690000000 + (i * 1000) for i in range(30)],
            "timestamp_updated": [1690000000 + (i * 1000) for i in range(30)],
        }
    )

    # 2. Configura rotulador de negócio
    regras = [
        {
            "identificador": "veteranos_ativos",
            "combinacao": "and",
            "condicoes": [
                {
                    "metrica": "mediana_horas_jogadas",
                    "operador": "maior_igual",
                    "valor": 50,
                },
            ],
            "rotulo": "jogadores_veteranos",
        }
    ]
    rotulador = RotuladorClusters.de_configuracao(regras)

    # 3. Observador MLflow (resiliente com fallback seguro)
    observador = ObservadorMlflow(
        tracking_uri="http://localhost:5000", falha_silenciosa=True
    )

    # 4. Executor completo
    executor = ExecutorTreinamento(
        configuracoes=config,
        observador_mlops=observador,
        rotulador_negocio=rotulador,
    )

    dados_gold, avaliacao, modelo = executor.executar_treinamento(
        dados_silver=dados_silver,
        nome_algoritmo="kmeans",
        parametros_algoritmo={"n_clusters": 3, "random_state": 42},
        versao_dataset="gold_teste_fase3",
    )

    # Verificações da etapa de Treinamento e Negócio
    assert not dados_gold.empty
    assert "cluster_id" in dados_gold.columns
    assert "rotulo_negocio" in dados_gold.columns
    assert avaliacao.total_clusters == 3
    assert modelo.capacidades.nome_algoritmo == "kmeans"

    # Verificação do Recuperador de Reviews (Inspeção Humana)
    recuperador = RecuperadorReviews()
    amostras = recuperador.recuperar_amostras_cluster(
        dados_gold, cluster_id=0, quantidade=3
    )
    assert len(amostras) > 0
    assert "Review textual" in amostras[0].review_texto

    # Verificação das Visualizações e Painel Executivo
    gerador = GeradorGraficos(amostragem_maxima=50)
    json_dispersao = gerador.gerar_dispersao_2d(
        dados_gold, "playtime_forever", "votes_up"
    )
    assert len(json_dispersao) > 50

    painel = PainelExecutivo()
    relatorio_md = painel.compilar_relatorio_markdown(
        metricas=avaliacao,
        nome_algoritmo="kmeans",
        mapa_rotulos_negocio={0: "jogadores_veteranos"},
        dados_gold=dados_gold,
    )
    assert "jogadores_veteranos" in relatorio_md
    assert "Relatório Executivo" in relatorio_md
