"""Testes unitários e de integração para o pacote de integração MLflow."""

import numpy as np
from sklearn.datasets import make_blobs

from app.agrupamento_modelos.agrupador_kmeans import AgrupadorKMeans
from app.integracao_mlflow.observador_mlflow import ObservadorMlflow
from app.integracao_mlflow.observador_nulo import ObservadorNulo
from app.integracao_mlflow.registro_modelos import RegistroModelos
from app.preprocessamento_ml.fabrica_preprocessamento import FabricaPreprocessamento


def teste_observador_nulo_execucao_segura() -> None:
    """Garante que o Null Object executa todos os métodos sem efeitos colaterais ou erros."""
    obs = ObservadorNulo()
    obs.registrar_inicio("exp_teste", "run_teste", {"p1": 10}, {"ambiente": "teste"})
    obs.registrar_metricas({"silhouette": 0.75, "db": 0.4})
    obs.registrar_artefato_texto("conteudo", "arquivo.txt")
    obs.registrar_artefato_dicionario({"chave": "valor"}, "dados.json")
    obs.registrar_distribuicao_clusters(np.array([0, 0, 1, 1, -1]))
    obs.registrar_fim()


def teste_observador_mlflow_integracao_ou_resiliencia() -> None:
    """Verifica se o ObservadorMlflow opera de forma resiliente e executa o fluxo completo."""
    obs = ObservadorMlflow(tracking_uri="http://localhost:5000", falha_silenciosa=True)
    obs.registrar_inicio(
        nome_experimento="steam_reviews_clustering_teste",
        nome_execucao="teste_run_unitario",
        parametros={"n_clusters": 3, "random_state": 42},
        tags={"modulo": "teste_mlflow"},
    )
    obs.registrar_metricas({"silhouette": 0.65, "davies_bouldin": 0.52})
    obs.registrar_distribuicao_clusters(np.array([0, 0, 0, 1, 1, 2, 2, -1]))
    obs.registrar_artefato_texto("teste artefato", "nota.txt")
    obs.registrar_artefato_dicionario({"k": 3, "status": "ok"}, "metadados.json")
    obs.registrar_fim()


def teste_registro_modelos_empacotamento() -> None:
    """Valida a serialização e registro de pipeline de pré-processamento e modelo."""
    retorno_blobs = make_blobs(n_samples=50, n_features=4, centers=3, random_state=42)
    x_dados = np.asarray(retorno_blobs[0], dtype=np.float64)

    fabrica = FabricaPreprocessamento()
    pipeline = fabrica.construir_pipeline(
        imputacao_ativada=True,
        tecnica_imputacao="median",
        escalonamento_ativado=True,
        tecnica_escalonamento="standard_scaler",
    )
    matriz_proc = pipeline.ajustar_e_transformar(x_dados)

    kmeans = AgrupadorKMeans(n_clusters=3, random_state=42)
    kmeans.treinar(matriz_proc)

    registrador = RegistroModelos(falha_silenciosa=True)
    registrador.registrar_pipeline_completo(
        pipeline=pipeline,
        algoritmo=kmeans,
        nomes_colunas_treino=["col_0", "col_1", "col_2", "col_3"],
        versao_dataset="gold_v1_teste",
        hash_configuracao="sha256_mock_hash",
    )
