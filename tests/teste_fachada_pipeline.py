"""Testes unitários para a FachadaPipelineClustering ponta a ponta."""

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from app.conf_yaml import (
    ConfigAlgoritmosClustering,
    ConfigAnalisesInfo,
    ConfigAtributosInfo,
    ConfigClusteringInfo,
    ConfigFonteInfo,
    ConfigMLflowInfo,
    ConfigParametrosKMeans,
    ConfigPreprocessamentoInfo,
    ConfigProcessamentoInfo,
    ConfigTreinoAtributos,
)
from app.contratos.fonte_dados import ProtocoloFonteDados
from app.contratos.repositorio import ProtocoloRepositorioLakehouse
from app.fachada_pipeline import FachadaPipelineClustering


@pytest.fixture
def dados_bronze_exemplo() -> pd.DataFrame:
    """Retorna dataframe simulando registros brutos da camada Bronze."""
    return pd.DataFrame(
        {
            "recommendationid": [f"rec_{i}" for i in range(20)],
            "review": [f"texto de avaliacao {i}" for i in range(20)],
            "voted_up": [i % 2 == 0 for i in range(20)],
            "votes_up": [float(i * 2) for i in range(20)],
            "votes_funny": [float(i) for i in range(20)],
            "author_playtime_forever": [float((i + 1) * 60) for i in range(20)],
            "author_playtime_last_two_weeks": [float(i * 10) for i in range(20)],
        }
    )


def test_fachada_pipeline_execucao_completa(
    dados_bronze_exemplo: pd.DataFrame,
    tmp_path: Path,
) -> None:
    """Verifica orquestração integrada ponta a ponta através da Fachada."""
    repo_mock = MagicMock(spec=ProtocoloRepositorioLakehouse)
    repo_mock.ler_bronze.return_value = dados_bronze_exemplo
    repo_mock.gravar_silver.return_value = "s3://steam-reviews/silver/730/20261025.parquet"
    repo_mock.gravar_gold.return_value = "s3://steam-reviews/gold/730/20261025.parquet"

    fonte_mock = MagicMock(spec=ProtocoloFonteDados)

    config_fonte = ConfigFonteInfo(tipo="steam_api")
    config_proc = ConfigProcessamentoInfo(motor="pandas")
    config_atrib = ConfigAtributosInfo(
        identificadores=["recommendationid"],
        treino=ConfigTreinoAtributos(
            colunas=[
                "votes_up",
                "votes_funny",
                "author_playtime_forever",
                "author_playtime_last_two_weeks",
            ]
        ),
    )
    config_preproc = ConfigPreprocessamentoInfo()
    config_clust = ConfigClusteringInfo(
        algoritmo="kmeans",
        algoritmos=ConfigAlgoritmosClustering(
            kmeans=ConfigParametrosKMeans(n_clusters=3),
        ),
    )
    config_mlflow = ConfigMLflowInfo(habilitado=False)
    config_analises = ConfigAnalisesInfo()

    fachada = FachadaPipelineClustering(
        config_fonte=config_fonte,
        config_processamento=config_proc,
        config_atributos=config_atrib,
        config_preprocessamento=config_preproc,
        config_clustering=config_clust,
        config_mlflow=config_mlflow,
        config_analises=config_analises,
        repositorio_lakehouse=repo_mock,
        fonte_dados=fonte_mock,
    )

    caminho_relatorio = tmp_path / "relatorio_final.html"

    resultado = fachada.executar(
        identificador=730,
        coletar_dados_novos=False,
        caminho_exportacao_relatorio=caminho_relatorio,
    )

    assert resultado.sucesso is True
    assert resultado.identificador == 730
    assert resultado.total_registros_processados == 20
    assert len(resultado.resultado_clustering.rotulos) == 20
    assert len(set(resultado.resultado_clustering.rotulos)) <= 3
    assert resultado.metricas.quantidade_clusters == 3
    assert resultado.resumo_analitico.total_amostras == 20
    assert "pca_2d" in resultado.figuras_geradas
    assert "distribuicao" in resultado.figuras_geradas
    assert "dispersao_2d" in resultado.figuras_geradas
    assert "perfil" in resultado.figuras_geradas
    assert "resumo" in resultado.figuras_geradas
    assert caminho_relatorio.exists()
    assert resultado.caminho_relatorio_html == str(caminho_relatorio)

    # Verifica chamadas ao repositório
    repo_mock.ler_bronze.assert_called_once_with(730)
    repo_mock.gravar_silver.assert_called_once()
    assert repo_mock.gravar_gold.call_count >= 2
