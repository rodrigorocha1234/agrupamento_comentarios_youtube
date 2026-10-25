"""Testes unitários para a camada de engenharia de atributos e pré-processamento de ML."""

from collections.abc import Sequence
from typing import override

import numpy as np
import pandas as pd
import pytest

from app.conf_yaml import (
    ConfigAtributosInfo,
    ConfigAvaliacaoAtributos,
    ConfigEscalonamento,
    ConfigPreprocessamentoInfo,
    ConfigReducaoDimensional,
    ConfigTextoAtributos,
    ConfigTransformacoesNumericas,
    ConfigTreinoAtributos,
    ConfigValoresAusentes,
)
from app.contratos.repositorio import ProtocoloRepositorioLakehouse
from app.excecoes import ErroPreprocessamento
from app.preprocessamento_ml.engenheiro_atributos import EngenheiroAtributos
from app.preprocessamento_ml.preparador_dados import PreparadorDados
from app.preprocessamento_ml.transformadores import FabricaTransformadores


class RepositorioGoldFake(ProtocoloRepositorioLakehouse):
    """Mock de repositório Lakehouse para verificar gravação da camada Gold."""

    def __init__(self) -> None:
        self.gold_salvo: dict[str, pd.DataFrame] = {}

    @override
    def gravar_bronze(self, identificador: str | int, registros: Sequence[dict[str, object]]) -> str:
        return ""

    @override
    def gravar_silver(self, identificador: str | int, dados: pd.DataFrame) -> str:
        return ""

    @override
    def gravar_gold(self, identificador: str | int, dados: pd.DataFrame, sufixo_visao: str) -> str:
        chave = f"{identificador}/{sufixo_visao}"
        self.gold_salvo[chave] = dados.copy()
        return f"s3://datalake-bucket/gold/{chave}.parquet"

    @override
    def ler_silver(self, identificador: str | int) -> pd.DataFrame:
        return pd.DataFrame()

    @override
    def ler_gold(self, identificador: str | int, sufixo_visao: str) -> pd.DataFrame:
        return self.gold_salvo.get(f"{identificador}/{sufixo_visao}", pd.DataFrame())


@pytest.fixture
def config_atributos_padrao() -> ConfigAtributosInfo:
    return ConfigAtributosInfo(
        identificadores=["recommendationid", "steamid", "appid"],
        treino=ConfigTreinoAtributos(
            colunas=["playtime_forever", "votes_up", "votes_funny", "voted_up"]
        ),
        avaliacao=ConfigAvaliacaoAtributos(colunas=["review", "timestamp_created"]),
        texto=ConfigTextoAtributos(incluir_no_treino=False),
    )


def test_preparador_isola_identificadores_e_texto(config_atributos_padrao: ConfigAtributosInfo) -> None:
    """Garante que nenhum identificador nem review chegam à matriz de treino."""
    df_silver = pd.DataFrame(
        {
            "recommendationid": ["rec_1", "rec_2"],
            "steamid": ["user_1", "user_2"],
            "appid": [730, 730],
            "review": ["Bom jogo", "Jogo ruim"],
            "timestamp_created": [1600000000, 1600000010],
            "playtime_forever": [120.0, 300.0],
            "votes_up": [5, 12],
            "votes_funny": [0, 1],
            "voted_up": [True, False],
        }
    )

    preparador = PreparadorDados(config_atributos_padrao)
    df_treino, df_metadados = preparador.preparar(df_silver)

    # Asserções estritas de isolamento
    assert "recommendationid" not in df_treino.columns
    assert "steamid" not in df_treino.columns
    assert "appid" not in df_treino.columns
    assert "review" not in df_treino.columns
    assert "timestamp_created" not in df_treino.columns

    # Verifica que colunas numéricas de treino foram preservadas
    assert list(df_treino.columns) == ["playtime_forever", "votes_up", "votes_funny", "voted_up"]
    assert df_treino["voted_up"].iloc[0] == 1.0
    assert df_treino["voted_up"].iloc[1] == 0.0

    # Metadados contêm os identificadores e reviews com index sincronizado
    assert "recommendationid" in df_metadados.columns
    assert "review" in df_metadados.columns
    assert len(df_metadados) == len(df_treino)


def test_preparador_falha_se_colunas_treino_ausentes(config_atributos_padrao: ConfigAtributosInfo) -> None:
    """Verifica lançamento de ErroPreprocessamento se nenhuma coluna de treino estiver presente."""
    df_invalido = pd.DataFrame({"coluna_estranha": [1, 2]})
    preparador = PreparadorDados(config_atributos_padrao)

    with pytest.raises(ErroPreprocessamento, match="Nenhuma coluna de treino válida encontrada"):
        preparador.preparar(df_invalido)


def test_pipeline_imputacao_e_escalonamento() -> None:
    """Verifica a esteira scikit-learn com SimpleImputer e StandardScaler."""
    config_prep = ConfigPreprocessamentoInfo(
        habilitado=True,
        valores_ausentes=ConfigValoresAusentes(estrategia="median"),
        escalonamento=ConfigEscalonamento(estrategia="standard"),
    )

    pipeline = FabricaTransformadores.criar_pipeline(config_prep)

    # Dados com NaNs e valores variados
    dados = pd.DataFrame(
        {
            "horas": [10.0, 20.0, np.nan, 40.0],
            "votos": [100.0, 200.0, 300.0, 400.0],
        }
    )

    resultado = pipeline.fit_transform(dados)

    assert resultado.shape == (4, 2)
    # StandardScaler resulta em média próxima a 0
    assert np.isclose(np.mean(resultado[:, 1]), 0.0, atol=1e-5)
    # Sem NaNs no resultado transformado
    assert not np.isnan(resultado).any()


def test_pipeline_transformacao_log1p_e_minmax() -> None:
    """Verifica encadeamento de log1p seguro seguido de MinMax scaler."""
    config_prep = ConfigPreprocessamentoInfo(
        habilitado=True,
        valores_ausentes=ConfigValoresAusentes(estrategia="constant", valor_constante=0.0),
        transformacoes_numericas=ConfigTransformacoesNumericas(habilitado=True, estrategia="log1p"),
        escalonamento=ConfigEscalonamento(estrategia="minmax"),
    )

    pipeline = FabricaTransformadores.criar_pipeline(config_prep)
    dados = pd.DataFrame({"horas": [0.0, 10.0, 100.0, 1000.0]})

    resultado = pipeline.fit_transform(dados)

    # MinMax escala para o intervalo [0.0, 1.0]
    assert np.isclose(np.min(resultado), 0.0)
    assert np.isclose(np.max(resultado), 1.0)


def test_pipeline_reducao_dimensional_pca() -> None:
    """Verifica a redução de dimensionalidade via PCA."""
    config_prep = ConfigPreprocessamentoInfo(
        habilitado=True,
        valores_ausentes=ConfigValoresAusentes(estrategia="median"),
        escalonamento=ConfigEscalonamento(estrategia="standard"),
        reducao_dimensional=ConfigReducaoDimensional(habilitado=True, estrategia="pca", componentes=2),
    )

    pipeline = FabricaTransformadores.criar_pipeline(config_prep)
    dados = pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0, 4.0, 5.0],
            "b": [10.0, 20.0, 30.0, 40.0, 50.0],
            "c": [100.0, 200.0, 300.0, 400.0, 500.0],
            "d": [5.0, 4.0, 3.0, 2.0, 1.0],
        }
    )

    resultado = pipeline.fit_transform(dados)
    assert resultado.shape == (5, 2)


def test_engenheiro_atributos_geracao_e_persistencia_gold(
    config_atributos_padrao: ConfigAtributosInfo,
) -> None:
    """Verifica o fluxo completo de transformação e gravação da camada Gold."""
    df_silver = pd.DataFrame(
        {
            "recommendationid": ["r1", "r2", "r3"],
            "steamid": ["s1", "s2", "s3"],
            "appid": [730, 730, 730],
            "review": ["Muito bom", "Regular", "Péssimo"],
            "timestamp_created": [1600000000, 1600000001, 1600000002],
            "playtime_forever": [10.0, 50.0, 200.0],
            "votes_up": [0, 5, 20],
            "votes_funny": [0, 0, 1],
            "voted_up": [False, True, True],
        }
    )

    config_prep = ConfigPreprocessamentoInfo(
        habilitado=True,
        valores_ausentes=ConfigValoresAusentes(estrategia="median"),
        escalonamento=ConfigEscalonamento(estrategia="standard"),
    )

    repo = RepositorioGoldFake()
    engenheiro = EngenheiroAtributos(config_atributos=config_atributos_padrao)

    resultado = engenheiro.processar_e_persistir_gold(
        identificador=730,
        dados_silver=df_silver,
        config_preprocessamento=config_prep,
        repositorio=repo,
    )

    # 1. Verifica resultado retornado
    assert isinstance(resultado.matriz_treino, pd.DataFrame)
    assert resultado.matriz_treino.shape == (3, 4)
    assert list(resultado.matriz_treino.columns) == [
        "playtime_forever",
        "votes_up",
        "votes_funny",
        "voted_up",
    ]

    # 2. Metadados segregados
    assert list(resultado.metadados["recommendationid"]) == ["r1", "r2", "r3"]
    assert "review" in resultado.metadados.columns

    # 3. Persistência na camada Gold
    assert "730/matriz_treino" in repo.gold_salvo
    assert "730/metadados" in repo.gold_salvo
    assert resultado.uri_gold_matriz.startswith("s3://datalake-bucket/gold/730/matriz_treino.parquet")
    assert resultado.uri_gold_metadados.startswith("s3://datalake-bucket/gold/730/metadados.parquet")
