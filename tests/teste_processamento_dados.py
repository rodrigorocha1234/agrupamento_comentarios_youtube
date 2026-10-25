"""Testes unitários para o processador de tabelas e avaliador de expressões."""

import numpy as np
import pandas as pd
import pytest

from app.conf_yaml import (
    ConfigColunasProcessamento,
    ConfigCondicaoFiltro,
    ConfigCriacaoColunas,
    ConfigFiltrosProcessamento,
    ConfigItemColuna,
    ConfigNovoAtributo,
    ConfigOperacaoTransformacao,
    ConfigProcessamentoInfo,
    ConfigTransformacoesProcessamento,
)
from app.excecoes import ErroPreprocessamento
from app.processamento_dados.avaliador_expressao import AvaliadorExpressao
from app.processamento_dados.processador_tabela import ProcessadorTabela


def test_ordem_transformacao_primeiro_criacao_depois() -> None:
    """Comprova que no código a transformação de colunas ocorre PRIMEIRO e a criação de novas colunas DEPOIS."""
    # Dado original com valor 100
    df = pd.DataFrame({"horas": [100.0, 200.0]})

    # Configuração:
    # 1. Transformação via expressão customizável: dividir horas por 2 (100 -> 50, 200 -> 100)
    # 2. Criação de coluna 'horas_ajustadas_mais_dez': horas + 10
    # Se transformação ocorrer PRIMEIRO: 50 + 10 = 60
    # Se criação ocorresse antes: 100 + 10 = 110
    config = ConfigProcessamentoInfo(
        motor="pandas",
        transformacoes=ConfigTransformacoesProcessamento(
            habilitado=True,
            operacoes=[
                ConfigOperacaoTransformacao(
                    coluna="horas",
                    habilitado=True,
                    expressao_pandas="df['horas'] / 2.0",
                    expressao_polars="pl.col('horas') / 2.0",
                )
            ],
        ),
        criacao_colunas=ConfigCriacaoColunas(
            habilitado=True,
            atributos=[
                ConfigNovoAtributo(
                    nome="horas_ajustadas_mais_dez",
                    habilitado=True,
                    expressao_pandas="df['horas'] + 10.0",
                    expressao_polars="pl.col('horas') + 10.0",
                )
            ],
        ),
    )

    processador = ProcessadorTabela()
    resultado = processador.processar(df, config)

    # Verifica que horas foi transformada primeiro (100 / 2 = 50)
    assert resultado["horas"].iloc[0] == 50.0
    # Verifica que a nova coluna usou o valor transformado primeiro (50 + 10 = 60)
    assert resultado["horas_ajustadas_mais_dez"].iloc[0] == 60.0
    assert resultado["horas_ajustadas_mais_dez"].iloc[1] == 110.0


def test_atributos_com_flag_false_por_padrao_nao_sao_criados() -> None:
    """Garante que atributos com habilitado: false não são criados."""
    df = pd.DataFrame({"playtime": [10, 20], "votes": [1, 2]})

    config = ConfigProcessamentoInfo(
        criacao_colunas=ConfigCriacaoColunas(
            habilitado=True,
            atributos=[
                ConfigNovoAtributo(
                    nome="coluna_desabilitada",
                    habilitado=False,  # Padrão é False
                    expressao_pandas="df['votes'] * 2",
                )
            ],
        )
    )

    processador = ProcessadorTabela()
    resultado = processador.processar(df, config)

    assert "coluna_desabilitada" not in resultado.columns


def test_criacao_colunas_motor_polars() -> None:
    """Verifica que a criação de colunas funciona com o motor Polars."""
    df = pd.DataFrame({"votos": [10.0, 20.0], "tempo": [100.0, 200.0]})

    config = ConfigProcessamentoInfo(
        motor="polars",
        criacao_colunas=ConfigCriacaoColunas(
            habilitado=True,
            atributos=[
                ConfigNovoAtributo(
                    nome="razao",
                    habilitado=True,
                    expressao_polars="pl.col('votos') / pl.col('tempo')",
                )
            ],
        ),
    )

    processador = ProcessadorTabela()
    resultado = processador.processar(df, config)

    assert "razao" in resultado.columns
    assert np.isclose(resultado["razao"].iloc[0], 0.1)


def test_bloqueio_expressao_insegura() -> None:
    """Garante que tentativas de importação ou acessos perigosos na expressão disparam ErroPreprocessamento."""
    df = pd.DataFrame({"x": [1, 2]})
    avaliador = AvaliadorExpressao()

    with pytest.raises(ErroPreprocessamento, match="Identificador '__import__' não é autorizado"):
        avaliador.avaliar_pandas("__import__('os').system('ls')", df)

    with pytest.raises(ErroPreprocessamento, match="Acesso a membros privados"):
        avaliador.avaliar_pandas("df.__class__", df)


def test_filtros_desabilitados_por_padrao_mantem_dados() -> None:
    """Verifica que quando filtros estão desabilitados, todos os dados são mantidos."""
    df = pd.DataFrame({"playtime": [10, 50, 100]})
    config = ConfigProcessamentoInfo(
        filtros=ConfigFiltrosProcessamento(
            habilitado=False,
            condicoes=[
                ConfigCondicaoFiltro(
                    nome="minimo_playtime",
                    habilitado=False,
                    expressao_pandas="df['playtime'] >= 60",
                )
            ],
        )
    )
    processador = ProcessadorTabela()
    resultado = processador.processar(df, config)
    assert len(resultado) == 3


def test_filtros_expressao_pandas() -> None:
    """Verifica a aplicação de filtro booleano usando expressão Pandas."""
    df = pd.DataFrame({"playtime": [10, 50, 100], "votes": [0, 5, 10]})
    config = ConfigProcessamentoInfo(
        motor="pandas",
        filtros=ConfigFiltrosProcessamento(
            habilitado=True,
            combinacao="and",
            condicoes=[
                ConfigCondicaoFiltro(
                    nome="minimo_playtime",
                    habilitado=True,
                    expressao_pandas="df['playtime'] >= 50",
                ),
                ConfigCondicaoFiltro(
                    nome="com_votos",
                    habilitado=True,
                    expressao_pandas="df['votes'] > 0",
                ),
            ],
        ),
    )
    processador = ProcessadorTabela()
    resultado = processador.processar(df, config)
    assert len(resultado) == 2
    assert list(resultado["playtime"]) == [50, 100]


def test_filtros_expressao_polars() -> None:
    """Verifica a aplicação de filtro booleano usando expressão Polars."""
    df = pd.DataFrame({"playtime": [10, 50, 100]})
    config = ConfigProcessamentoInfo(
        motor="polars",
        filtros=ConfigFiltrosProcessamento(
            habilitado=True,
            combinacao="and",
            condicoes=[
                ConfigCondicaoFiltro(
                    nome="minimo_playtime",
                    habilitado=True,
                    expressao_polars="pl.col('playtime') >= 60",
                )
            ],
        ),
    )
    processador = ProcessadorTabela()
    resultado = processador.processar(df, config)
    assert len(resultado) == 1
    assert resultado["playtime"].iloc[0] == 100


def test_selecao_colunas_desabilitada_por_padrao_mantem_todas() -> None:
    """Verifica que com colunas.habilitado = False por padrão, todas as colunas são mantidas."""
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
    config = ConfigProcessamentoInfo(
        colunas=ConfigColunasProcessamento(
            habilitado=False,  # Falso por padrão
            incluir=["a"],
        )
    )
    processador = ProcessadorTabela()
    resultado = processador.processar(df, config)
    assert list(resultado.columns) == ["a", "b", "c"]


def test_selecao_colunas_habilitada_filtra_colunas() -> None:
    """Verifica que quando habilitada, apenas as colunas especificadas são mantidas."""
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
    config = ConfigProcessamentoInfo(
        colunas=ConfigColunasProcessamento(
            habilitado=True,
            incluir=[
                ConfigItemColuna(nome="a", habilitado=True),
                ConfigItemColuna(nome="b", habilitado=False),
                "c",
            ],
        )
    )
    processador = ProcessadorTabela()
    resultado = processador.processar(df, config)
    assert list(resultado.columns) == ["a", "c"]


def test_selecao_colunas_com_chave_selecao_colunas() -> None:
    """Verifica a seleção de colunas configurada pelo campo selecao_colunas."""
    df = pd.DataFrame({"col_x": [10], "col_y": [20], "col_z": [30]})
    config = ConfigProcessamentoInfo(
        selecao_colunas=ConfigColunasProcessamento(
            habilitado=True,
            colunas=[
                ConfigItemColuna(nome="col_x", habilitado=True),
                ConfigItemColuna(nome="col_y", habilitado=False),
                ConfigItemColuna(nome="col_z", habilitado=False),
            ],
        )
    )
    processador = ProcessadorTabela()
    resultado = processador.processar(df, config)
    assert list(resultado.columns) == ["col_x"]


def test_transformacao_colunas_motor_polars() -> None:
    """Verifica a transformação de coluna existente com expressão declarativa Polars."""
    df = pd.DataFrame({"valor": [10.0, 30.0]})
    config = ConfigProcessamentoInfo(
        motor="polars",
        transformacoes=ConfigTransformacoesProcessamento(
            habilitado=True,
            operacoes=[
                ConfigOperacaoTransformacao(
                    coluna="valor",
                    habilitado=True,
                    expressao_polars="pl.col('valor') * 2.0",
                )
            ],
        ),
    )
    processador = ProcessadorTabela()
    resultado = processador.processar(df, config)
    assert list(resultado["valor"]) == [20.0, 60.0]


def test_transformacao_desabilitada_por_padrao_mantem_original() -> None:
    """Verifica que transformações com habilitado: false por padrão não alteram a coluna."""
    df = pd.DataFrame({"valor": [10.0, 30.0]})
    config = ConfigProcessamentoInfo(
        motor="pandas",
        transformacoes=ConfigTransformacoesProcessamento(
            habilitado=True,
            operacoes=[
                ConfigOperacaoTransformacao(
                    coluna="valor",
                    habilitado=False,  # Falso por padrão
                    expressao_pandas="df['valor'] * 100.0",
                )
            ],
        ),
    )
    processador = ProcessadorTabela()
    resultado = processador.processar(df, config)
    assert list(resultado["valor"]) == [10.0, 30.0]


