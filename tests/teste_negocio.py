"""Testes unitários para o motor de regras de negócio pós-treinamento."""

import pandas as pd

from app.regras_negocio.especificacao_negocio import (
    EspecificacaoCompostaAnd,
    EspecificacaoCompostaOr,
    EspecificacaoCondicao,
)
from app.regras_negocio.rotulador_clusters import RotuladorClusters


def teste_especificacao_condicao_operadores() -> None:
    """Verifica a avaliação de operadores atômicos da especificação."""
    cond_maior = EspecificacaoCondicao("idade", "maior", 18)
    assert cond_maior.satisfeita_por({"idade": 25})
    assert not cond_maior.satisfeita_por({"idade": 17})

    cond_entre = EspecificacaoCondicao("horas", "entre", [10, 50])
    assert cond_entre.satisfeita_por({"horas": 30})
    assert not cond_entre.satisfeita_por({"horas": 5})


def teste_especificacao_composite_and_or() -> None:
    """Valida a composição lógica de predicados de negócio."""
    cond1 = EspecificacaoCondicao("horas", "maior_igual", 100)
    cond2 = EspecificacaoCondicao("negativas", "maior_igual", 60)

    regra_and = EspecificacaoCompostaAnd([cond1, cond2])
    assert regra_and.satisfeita_por({"horas": 150, "negativas": 70})
    assert not regra_and.satisfeita_por({"horas": 150, "negativas": 50})

    regra_or = EspecificacaoCompostaOr([cond1, cond2])
    assert regra_or.satisfeita_por({"horas": 50, "negativas": 80})
    assert not regra_or.satisfeita_por({"horas": 20, "negativas": 10})


def teste_rotulagem_sem_alterar_clusters_originais() -> None:
    """Garante que a rotulagem enriqueça o DataFrame sem alterar IDs numéricos de clusters."""
    dados = pd.DataFrame(
        {
            "recommendationid": ["rec_1", "rec_2", "rec_3", "rec_4"],
            "cluster_id": [0, 0, 1, -1],
            "horas_jogadas_total": [120.0, 150.0, 10.0, 50.0],
            "voted_up": [False, False, True, True],
        }
    )

    regras_config = [
        {
            "identificador": "experientes_insatisfeitos",
            "combinacao": "and",
            "condicoes": [
                {
                    "metrica": "mediana_horas_jogadas",
                    "operador": "maior_igual",
                    "valor": 100,
                },
                {
                    "metrica": "percentual_reviews_negativas",
                    "operador": "maior_igual",
                    "valor": 50,
                },
            ],
            "rotulo": "jogadores_veteranos_criticos",
        },
        {
            "identificador": "novatos_satisfeitos",
            "combinacao": "and",
            "condicoes": [
                {"metrica": "mediana_horas_jogadas", "operador": "menor", "valor": 50},
                {
                    "metrica": "percentual_reviews_positivas",
                    "operador": "maior_igual",
                    "valor": 50,
                },
            ],
            "rotulo": "novatos_empolgados",
        },
    ]

    rotulador = RotuladorClusters.de_configuracao(regras_config)
    df_rotulado, mapa = rotulador.rotular_clusters(dados)

    # 1. Os IDs originais de cluster continuam idênticos
    assert list(df_rotulado["cluster_id"]) == [0, 0, 1, -1]

    # 2. Rótulos atribuídos corretamente conforme as regras
    assert mapa[0] == "jogadores_veteranos_criticos"
    assert mapa[1] == "novatos_empolgados"
    assert mapa[-1] == "ruido_estatistico"

    # 3. Coluna rotulo_negocio gerada com precisão
    assert df_rotulado.loc[0, "rotulo_negocio"] == "jogadores_veteranos_criticos"
    assert df_rotulado.loc[2, "rotulo_negocio"] == "novatos_empolgados"
    assert df_rotulado.loc[3, "rotulo_negocio"] == "ruido_estatistico"
