"""Testes para engenharia de atributos tabulares e segregação de matrizes."""

import pandas as pd
import pytest

from app.engenharia_atributos.gerador_atributos import GeradorAtributosDerivados
from app.engenharia_atributos.seletor_colunas import SeletorColunasTreinamento


def teste_geracao_atributos_derivados() -> None:
    """Verifica cálculo correto de variáveis derivadas temporais e de engajamento."""
    gerador = GeradorAtributosDerivados()
    df = pd.DataFrame(
        {
            "playtime_at_review": [120.0, 300.0],
            "playtime_forever": [240.0, 600.0],
            "playtime_last_two_weeks": [60.0, 0.0],
            "last_played": [1700000000, 1699913600],
        }
    )

    resultado = gerador.calcular_atributos(df, timestamp_referencia=1700086400)

    # horas_ate_review = minutos / 60
    assert list(resultado["horas_ate_review"]) == [2.0, 5.0]

    # horas_apos_review = (playtime_forever - playtime_at_review) / 60
    assert list(resultado["horas_apos_review"]) == [2.0, 5.0]

    # dias_desde_ultima_atividade = (1700086400 - 1700000000) / 86400 = 1.0 dia
    assert resultado["dias_desde_ultima_atividade"].iloc[0] == 1.0

    # proporcao_jogo_recente = 60 / (240 + 1)
    assert resultado["proporcao_jogo_recente"].iloc[0] == pytest.approx(60.0 / 241.0)


def teste_seletor_colunas_isolamento_estrito() -> None:
    """Garante que colunas de identificação e texto de reviews sejam expurgadas de X."""
    seletor = SeletorColunasTreinamento()
    df = pd.DataFrame(
        {
            "appid": [427520],
            "recommendationid": ["REC_123"],
            "steamid": ["76561198000000001"],
            "review_texto": ["Texto original que não deve vazar para X"],
            "playtime_forever": [1200.0],
            "num_reviews": [5.0],
        }
    )

    colunas_solicitadas = [
        "recommendationid",
        "review_texto",
        "playtime_forever",
        "num_reviews",
    ]
    matriz_x = seletor.extrair_matriz_treino(df, colunas_solicitadas)

    assert "recommendationid" not in matriz_x.columns
    assert "review_texto" not in matriz_x.columns
    assert list(matriz_x.columns) == ["playtime_forever", "num_reviews"]
    assert matriz_x.shape == (1, 2)


def teste_seletor_colunas_rejeita_sem_colunas_validas() -> None:
    """Levanta erro quando nenhuma coluna de treino válida for encontrada."""
    seletor = SeletorColunasTreinamento()
    df = pd.DataFrame({"recommendationid": ["123"], "steamid": ["456"]})

    with pytest.raises(ValueError):
        seletor.extrair_matriz_treino(df, ["recommendationid", "steamid"])
