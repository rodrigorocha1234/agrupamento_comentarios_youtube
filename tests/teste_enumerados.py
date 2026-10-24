"""Testes unitários para validação e integridade dos tipos enumerados do projeto."""

import pytest
from pydantic import BaseModel, ValidationError

from app.configuracao_geral.tipos_enumerados import (
    AlgoritmoVizinhos,
    CamadaLakehouse,
    DispositivoExecucao,
    GranularidadeTendencia,
    InicializacaoKMeans,
    JanelaTemporal,
    MetricaDistancia,
    MetodoSelecaoCluster,
    MotorProcessamento,
    NormaVetorizacao,
    OrigemComentario,
    PeriodicidadeColeta,
    StatusSaude,
    StatusTendencia,
    TecnicaCluster,
    TecnicaReducao,
    TecnicaRepresentacao,
    TipoFonteDados,
    TipoPersistencia,
    TipoProvedorVisualizacao,
)


class ModeloExemplo(BaseModel):
    tecnica: TecnicaCluster
    janela: JanelaTemporal
    camada: CamadaLakehouse
    status: StatusTendencia
    origem: OrigemComentario


def test_valores_tecnicas_cluster():
    """Valida valores e herança de StrEnum para clusterização."""
    assert TecnicaCluster.KMEANS == "kmeans"
    assert TecnicaCluster.DBSCAN == "dbscan"
    assert TecnicaCluster.HDBSCAN == "hdbscan"
    assert isinstance(TecnicaCluster.KMEANS, str)
    assert f"tecnica={TecnicaCluster.KMEANS}" == "tecnica=kmeans"


def test_valores_janelas_temporais():
    """Valida janelas temporais suportadas pelo pipeline."""
    assert JanelaTemporal.SETE_DIAS == "7dias"
    assert JanelaTemporal.QUINZE_DIAS == "15dias"
    assert JanelaTemporal.TRINTA_DIAS == "30dias"


def test_valores_status_tendencias():
    """Valida status de classificação temporal."""
    assert StatusTendencia.CRESCENDO == "crescendo"
    assert StatusTendencia.DECRESCENDO == "decrescendo"
    assert StatusTendencia.ESTAVEL == "estavel"
    assert StatusTendencia.NOVO == "novo"
    assert StatusTendencia.SEM_DADOS == "sem_dados"


def test_valores_camadas_lakehouse():
    """Valida arquitetura de medalhão do datalake."""
    assert CamadaLakehouse.BRONZE == "bronze"
    assert CamadaLakehouse.PRATA == "prata"
    assert CamadaLakehouse.OURO == "ouro"


def test_valores_origem_comentario():
    """Valida distinção entre comentários principais e respostas."""
    assert OrigemComentario.PRINCIPAL == "principal"
    assert OrigemComentario.RESPOSTA == "resposta"


def test_valores_tecnicas_vetorizacao_e_reducao():
    """Valida técnicas de NLP e redução dimensional."""
    assert TecnicaRepresentacao.TFIDF == "tfidf"
    assert TecnicaRepresentacao.BERTIMBAU == "bertimbau"
    assert TecnicaRepresentacao.COUNT == "count"

    assert TecnicaReducao.PCA == "pca"
    assert TecnicaReducao.SVD == "svd"
    assert TecnicaReducao.TSNE == "tsne"
    assert TecnicaReducao.UMAP == "umap"


def test_valores_periodicidade_e_saude():
    """Valida periodicidade de coleta e status de saúde."""
    assert PeriodicidadeColeta.DIARIA == "diaria"
    assert PeriodicidadeColeta.SEMANAL == "semanal"

    assert StatusSaude.SAUDAVEL == "saudavel"
    assert StatusSaude.DEGRADADO == "degradado"


def test_interoperabilidade_com_pydantic():
    """Garante que Pydantic serializa e valida instâncias a partir de strings literais."""
    dados = {
        "tecnica": "kmeans",
        "janela": "7dias",
        "camada": "ouro",
        "status": "crescendo",
        "origem": "principal",
    }
    modelo = ModeloExemplo.model_validate(dados)
    assert modelo.tecnica == TecnicaCluster.KMEANS
    assert modelo.janela == JanelaTemporal.SETE_DIAS
    assert modelo.camada == CamadaLakehouse.OURO
    assert modelo.status == StatusTendencia.CRESCENDO
    assert modelo.origem == OrigemComentario.PRINCIPAL

    with pytest.raises(ValidationError):
        ModeloExemplo.model_validate({**dados, "tecnica": "algoritmo_inexistente"})


def test_valores_motor_processamento() -> None:
    """Valida motores de processamento e manipulação tabular suportados."""
    assert MotorProcessamento.PANDAS == "pandas"
    assert MotorProcessamento.POLARS == "polars"
    assert isinstance(MotorProcessamento.POLARS, str)
    assert f"motor={MotorProcessamento.POLARS}" == "motor=polars"


def test_valores_novos_strenums_configuracao() -> None:
    """Valida domínio e integridade de todos os novos StrEnums de configuração."""
    assert NormaVetorizacao.L1 == "l1"
    assert NormaVetorizacao.L2 == "l2"

    assert DispositivoExecucao.CPU == "cpu"
    assert DispositivoExecucao.CUDA == "cuda"

    assert MetricaDistancia.COSINE == "cosine"
    assert MetricaDistancia.EUCLIDEAN == "euclidean"

    assert InicializacaoKMeans.KMEANS_PLUS_PLUS == "k-means++"
    assert InicializacaoKMeans.RANDOM == "random"

    assert MetodoSelecaoCluster.EOM == "eom"
    assert MetodoSelecaoCluster.LEAF == "leaf"

    assert AlgoritmoVizinhos.AUTO == "auto"
    assert AlgoritmoVizinhos.BALL_TREE == "ball_tree"
    assert AlgoritmoVizinhos.KD_TREE == "kd_tree"
    assert AlgoritmoVizinhos.BRUTE == "brute"

    assert GranularidadeTendencia.DIARIA == "diaria"
    assert GranularidadeTendencia.JANELA == "janela"

    assert TipoPersistencia.S3 == "s3"
    assert TipoPersistencia.LOCAL == "local"

    assert TipoFonteDados.YOUTUBE == "youtube"
    assert TipoFonteDados.CSV == "csv"
    assert TipoFonteDados.PARQUET == "parquet"
    assert TipoFonteDados.JSONL == "jsonl"
    assert TipoFonteDados.LOCAL == "local"

    assert TipoProvedorVisualizacao.GRAFANA == "grafana"
    assert TipoProvedorVisualizacao.NENHUM == "nenhum"
    assert TipoProvedorVisualizacao.CUSTOM == "custom"


