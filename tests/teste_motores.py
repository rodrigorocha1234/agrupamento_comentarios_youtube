"""Testes de paridade semântica entre os motores tabulares Pandas e Polars via DSL."""

import numpy as np
import pandas as pd
import polars as pl
import pytest

from app.processamento_dados.fabrica_motores import FabricaMotores
from app.processamento_dados.interpretador_dsl import ErroOperadorDslDesconhecido
from app.processamento_dados.motor_pandas import MotorPandas
from app.processamento_dados.motor_polars import MotorPolars


@pytest.fixture
def dados_exemplo() -> tuple[pd.DataFrame, pl.DataFrame]:
    """Fornece datasets idênticos em Pandas e Polars para comparação."""
    dados_dict = {
        "appid": [427520, 427520, 526870, 526870, 427520],
        "playtime_at_review": [60.0, 120.0, 180.0, 30.0, 300.0],
        "votes_up": [5, 10, 0, 2, 25],
        "voted_up": [True, True, False, False, True],
    }
    df_pd = pd.DataFrame(dados_dict)
    df_pl = pl.DataFrame(dados_dict)
    return df_pd, df_pl


def teste_paridade_filtros(dados_exemplo: tuple[pd.DataFrame, pl.DataFrame]) -> None:
    """Verifica que o filtro 'playtime_at_review >= 120' produz os mesmos registros em ambos os motores."""
    df_pd, df_pl = dados_exemplo
    motor_pd = MotorPandas()
    motor_pl = MotorPolars()

    condicoes = [
        {"coluna": "playtime_at_review", "operador": "maior_igual", "valor": 120.0}
    ]

    res_pd = motor_pd.aplicar_filtros(df_pd, condicoes, combinacao="and")
    res_pl = motor_pl.aplicar_filtros(df_pl, condicoes, combinacao="and")

    assert len(res_pd) == 3
    assert res_pl.height == 3
    assert np.allclose(
        res_pd["playtime_at_review"].to_numpy(),
        res_pl["playtime_at_review"].to_numpy(),
    )


def teste_paridade_criacao_atributos(
    dados_exemplo: tuple[pd.DataFrame, pl.DataFrame],
) -> None:
    """Verifica que a operação 'dividir_constante' produz valores idênticos."""
    df_pd, df_pl = dados_exemplo
    motor_pd = MotorPandas()
    motor_pl = MotorPolars()

    res_pd = motor_pd.criar_atributo(
        df_pd,
        nome="horas_ate_review",
        tecnica="dividir_constante",
        origem="playtime_at_review",
        valor=60.0,
    )
    res_pl = motor_pl.criar_atributo(
        df_pl,
        nome="horas_ate_review",
        tecnica="dividir_constante",
        origem="playtime_at_review",
        valor=60.0,
    )

    valores_pd = res_pd["horas_ate_review"].to_numpy()
    valores_pl = res_pl["horas_ate_review"].to_numpy()
    assert np.allclose(valores_pd, valores_pl)
    assert np.allclose(valores_pd, [1.0, 2.0, 3.0, 0.5, 5.0])


def teste_rejeicao_operador_desconhecido(
    dados_exemplo: tuple[pd.DataFrame, pl.DataFrame],
) -> None:
    """Garante erro de configuração quando um operador desconhecido for passado."""
    df_pd, _ = dados_exemplo
    motor_pd = MotorPandas()
    with pytest.raises(ErroOperadorDslDesconhecido):
        motor_pd.aplicar_filtros(
            df_pd,
            [
                {
                    "coluna": "playtime_at_review",
                    "operador": "operador_falso",
                    "valor": 10,
                }
            ],
        )


def teste_fabrica_motores() -> None:
    """Verifica resolução correta de motores via Registry da fábrica."""
    fabrica = FabricaMotores()
    motor_pd = fabrica.criar_motor("pandas")
    motor_pl = fabrica.criar_motor("polars")

    assert isinstance(motor_pd, MotorPandas)
    assert isinstance(motor_pl, MotorPolars)
