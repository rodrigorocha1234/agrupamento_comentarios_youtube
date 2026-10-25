"""Testes unitários para o motor declarativo de regras de negócio."""

import pandas as pd
import pytest

from app.analise_clusters.analisador_clusters import PerfilCluster
from app.conf_yaml import (
    ConfigAcaoRegra,
    ConfigRegraItem,
    ConfigRegrasNegocioInfo,
)
from app.regras_negocio.avaliador_regras import AvaliadorRegrasNegocio


@pytest.fixture
def config_regras_exemplo() -> ConfigRegrasNegocioInfo:
    """Configura regras de negócio para clusters e amostras via expressões seguras."""
    return ConfigRegrasNegocioInfo(
        habilitado=True,
        motor="pandas",
        regras=[
            ConfigRegraItem(
                nome="Veteranos Entusiastas",
                habilitado=True,
                alvo="cluster",
                expressao_pandas="(df['author_playtime_forever'] >= 100.0) & (df['taxa_recomendacao'] >= 0.8)",
                expressao_polars="(pl.col('author_playtime_forever') >= 100.0) & (pl.col('taxa_recomendacao') >= 0.8)",
                acao=ConfigAcaoRegra(
                    rotulo="Veteranos Satisfeitos",
                    alerta=False,
                    prioridade="baixa",
                ),
            ),
            ConfigRegraItem(
                nome="Críticos Relevantes",
                habilitado=True,
                alvo="cluster",
                expressao_pandas="(df['taxa_recomendacao'] <= 0.3) & (df['votes_up'] >= 5.0)",
                expressao_polars="(pl.col('taxa_recomendacao') <= 0.3) & (pl.col('votes_up') >= 5.0)",
                acao=ConfigAcaoRegra(
                    rotulo="Críticos Influentes",
                    alerta=True,
                    prioridade="alta",
                ),
            ),
            ConfigRegraItem(
                nome="Alerta Churn Veterano",
                habilitado=True,
                alvo="amostra",
                expressao_pandas="(~df['voted_up']) & (df['author_playtime_forever'] >= 300.0)",
                expressao_polars="(~pl.col('voted_up')) & (pl.col('author_playtime_forever') >= 300.0)",
                acao=ConfigAcaoRegra(
                    tag="churn_veterano",
                    alerta=True,
                    prioridade="critica",
                ),
            ),
        ],
    )


def test_regras_negocio_perfil_cluster(config_regras_exemplo: ConfigRegrasNegocioInfo) -> None:
    """Verifica anotação correta de personas e alertas de negócio nos clusters."""
    avaliador = AvaliadorRegrasNegocio(config_regras_exemplo)

    # 1. Cluster de veteranos satisfeitos
    perfil_vet = PerfilCluster(
        id_cluster=0,
        nome_rotulo="Cluster 0",
        quantidade_amostras=50,
        proporcao_amostras=0.5,
        medias_atributos={"author_playtime_forever": 150.0, "votes_up": 2.0},
        medianas_atributos={"author_playtime_forever": 140.0, "votes_up": 1.0},
        metricas_personalizadas={"taxa_recomendacao": 0.9},
    )
    perfil_anotado_vet = avaliador.aplicar_regras_perfil(perfil_vet)
    assert perfil_anotado_vet.rotulo_negocio == "Veteranos Satisfeitos"
    assert perfil_anotado_vet.alerta_negocio is False
    assert perfil_anotado_vet.prioridade_negocio == "baixa"

    # 2. Cluster de críticos relevantes
    perfil_crit = PerfilCluster(
        id_cluster=1,
        nome_rotulo="Cluster 1",
        quantidade_amostras=30,
        proporcao_amostras=0.3,
        medias_atributos={"author_playtime_forever": 40.0, "votes_up": 12.0},
        medianas_atributos={"author_playtime_forever": 35.0, "votes_up": 10.0},
        metricas_personalizadas={"taxa_recomendacao": 0.1},
    )
    perfil_anotado_crit = avaliador.aplicar_regras_perfil(perfil_crit)
    assert perfil_anotado_crit.rotulo_negocio == "Críticos Influentes"
    assert perfil_anotado_crit.alerta_negocio is True
    assert perfil_anotado_crit.prioridade_negocio == "alta"


def test_regras_negocio_amostras_sinalizacao(config_regras_exemplo: ConfigRegrasNegocioInfo) -> None:
    """Verifica criação de colunas de tags e alertas por amostra individual."""
    avaliador = AvaliadorRegrasNegocio(config_regras_exemplo)

    df_amostras = pd.DataFrame(
        {
            "recommendationid": ["1", "2", "3"],
            "voted_up": [False, True, False],
            "author_playtime_forever": [500.0, 600.0, 50.0],
        }
    )

    df_resultado = avaliador.aplicar_regras_amostras(df_amostras)

    assert "tag_churn_veterano" in df_resultado.columns
    assert "alerta_negocio" in df_resultado.columns

    # Linha 0: voted_up=False e playtime >= 300 -> True
    assert bool(df_resultado["tag_churn_veterano"].iloc[0]) is True
    assert bool(df_resultado["alerta_negocio"].iloc[0]) is True

    # Linha 1: voted_up=True -> False
    assert bool(df_resultado["tag_churn_veterano"].iloc[1]) is False

    # Linha 2: voted_up=False mas playtime < 300 -> False
    assert bool(df_resultado["tag_churn_veterano"].iloc[2]) is False


def test_regras_negocio_desabilitadas() -> None:
    """Verifica que quando desabilitado, os dados originais são devolvidos intactos."""
    config_desabilitada = ConfigRegrasNegocioInfo(habilitado=False)
    avaliador = AvaliadorRegrasNegocio(config_desabilitada)

    perfil = PerfilCluster(
        id_cluster=0,
        nome_rotulo="Cluster 0",
        quantidade_amostras=10,
        proporcao_amostras=1.0,
        medias_atributos={"votes_up": 5.0},
        medianas_atributos={"votes_up": 5.0},
    )
    assert avaliador.aplicar_regras_perfil(perfil) == perfil

    df = pd.DataFrame({"votes_up": [1, 2]})
    assert avaliador.aplicar_regras_amostras(df).equals(df)


def test_regras_negocio_combinacao_or() -> None:
    """Verifica regra com operador 'or' via expressão booleana."""
    config = ConfigRegrasNegocioInfo(
        habilitado=True,
        motor="pandas",
        regras=[
            ConfigRegraItem(
                nome="Extremo",
                habilitado=True,
                alvo="cluster",
                expressao_pandas="(df['taxa_recomendacao'] == 1.0) | (df['taxa_recomendacao'] == 0.0)",
                acao=ConfigAcaoRegra(rotulo="Consenso Extremo"),
            )
        ],
    )
    avaliador = AvaliadorRegrasNegocio(config)

    perfil_unanimidade = PerfilCluster(
        id_cluster=0,
        nome_rotulo="Cluster 0",
        quantidade_amostras=10,
        proporcao_amostras=1.0,
        medias_atributos={},
        medianas_atributos={},
        metricas_personalizadas={"taxa_recomendacao": 1.0},
    )
    assert avaliador.aplicar_regras_perfil(perfil_unanimidade).rotulo_negocio == "Consenso Extremo"


def test_regras_negocio_expressao_pandas() -> None:
    """Verifica avaliação de regras via expressões Python Pandas para amostras e clusters."""
    config = ConfigRegrasNegocioInfo(
        habilitado=True,
        motor="pandas",
        regras=[
            ConfigRegraItem(
                nome="Expressao Amostra Pandas",
                habilitado=True,
                alvo="amostra",
                expressao_pandas="(df['horas'] >= 100) & (~df['recomendou'])",
                acao=ConfigAcaoRegra(tag="churn_expressao", alerta=True, prioridade="critica"),
            ),
            ConfigRegraItem(
                nome="Expressao Cluster Pandas",
                habilitado=True,
                alvo="cluster",
                expressao_pandas="(df['media_horas_jogadas'] >= 80.0) & (df['taxa_recomendacao'] >= 0.8)",
                acao=ConfigAcaoRegra(rotulo="Veteranos Expressao", prioridade="alta"),
            ),
        ],
    )
    avaliador = AvaliadorRegrasNegocio(config)

    # 1. Teste amostras pandas
    df_amostras = pd.DataFrame(
        {
            "horas": [150.0, 50.0, 120.0],
            "recomendou": [False, False, True],
        }
    )
    res_amostras = avaliador.aplicar_regras_amostras(df_amostras)
    assert "tag_churn_expressao" in res_amostras.columns
    assert bool(res_amostras["tag_churn_expressao"].iloc[0]) is True
    assert bool(res_amostras["tag_churn_expressao"].iloc[1]) is False
    assert bool(res_amostras["tag_churn_expressao"].iloc[2]) is False

    # 2. Teste cluster pandas
    perfil_vet = PerfilCluster(
        id_cluster=0,
        nome_rotulo="Cluster 0",
        quantidade_amostras=40,
        proporcao_amostras=1.0,
        medias_atributos={},
        medianas_atributos={},
        metricas_personalizadas={"media_horas_jogadas": 100.0, "taxa_recomendacao": 0.85},
    )
    res_perfil = avaliador.aplicar_regras_perfil(perfil_vet)
    assert res_perfil.rotulo_negocio == "Veteranos Expressao"


def test_regras_negocio_expressao_polars() -> None:
    """Verifica avaliação de regras via expressões Python Polars para amostras e clusters."""
    config = ConfigRegrasNegocioInfo(
        habilitado=True,
        motor="polars",
        regras=[
            ConfigRegraItem(
                nome="Expressao Amostra Polars",
                habilitado=True,
                alvo="amostra",
                expressao_polars="(pl.col('pontos') > 50) & (pl.col('ativo'))",
                acao=ConfigAcaoRegra(tag="engajado_polars", prioridade="media"),
            ),
            ConfigRegraItem(
                nome="Expressao Cluster Polars",
                habilitado=True,
                alvo="cluster",
                expressao_polars="pl.col('quantidade_amostras') >= 100",
                acao=ConfigAcaoRegra(rotulo="Mega Cluster Polars"),
            ),
        ],
    )
    avaliador = AvaliadorRegrasNegocio(config)

    # 1. Teste amostras polars
    df_amostras = pd.DataFrame(
        {
            "pontos": [10, 60, 80],
            "ativo": [True, True, False],
        }
    )
    res_amostras = avaliador.aplicar_regras_amostras(df_amostras)
    assert "tag_engajado_polars" in res_amostras.columns
    assert bool(res_amostras["tag_engajado_polars"].iloc[0]) is False
    assert bool(res_amostras["tag_engajado_polars"].iloc[1]) is True
    assert bool(res_amostras["tag_engajado_polars"].iloc[2]) is False

    # 2. Teste cluster polars
    perfil_mega = PerfilCluster(
        id_cluster=1,
        nome_rotulo="Cluster 1",
        quantidade_amostras=150,
        proporcao_amostras=1.0,
        medias_atributos={},
        medianas_atributos={},
    )
    res_cluster = avaliador.aplicar_regras_perfil(perfil_mega)
    assert res_cluster.rotulo_negocio == "Mega Cluster Polars"
