"""Ponto de entrada principal da plataforma de clustering de avaliações."""

import argparse
import sys
from pathlib import Path

import uvicorn

from app.conf_yaml import ConfYAML
from app.fachada_pipeline import FachadaPipelineClustering
from app.gestao_datalake.repositorio_s3_lakehouse import RepositorioS3Lakehouse
from app.servico_api.aplicacao import criar_aplicacao_fastapi
from app.servico_api.estado_aplicacao import EstadoAplicacao


def executar_pipeline_cli(
    identificador: str | int,
    coletar: bool,
    caminho_relatorio: str | None,
) -> None:
    """Executa a esteira analítica completa da Fachada a partir da linha de comando."""
    diretorio_config = Path("config")
    print(f"[*] Carregando configurações YAML de '{diretorio_config}'...")
    conf = ConfYAML.carregar_de_diretorio(diretorio_config)

    print(f"[*] Inicializando Fachada do Pipeline para identificador '{identificador}'...")
    repositorio = RepositorioS3Lakehouse(config=conf.datalake.datalake)

    fachada = FachadaPipelineClustering(
        config_fonte=conf.fonte_dados.fonte,
        config_processamento=conf.processamento.processamento,
        config_atributos=conf.atributos.atributos,
        config_preprocessamento=conf.preprocessamento.preprocessamento,
        config_clustering=conf.clustering.clustering,
        config_mlflow=conf.mlflow.mlflow,
        config_analises=conf.analises.analises,
        repositorio_lakehouse=repositorio,
    )

    caminho_rel = caminho_relatorio or "relatorio_clusters.html"
    print(f"[*] Executando pipeline (coletar_dados_novos={coletar})...")
    resultado = fachada.executar(
        identificador=identificador,
        coletar_dados_novos=coletar,
        caminho_exportacao_relatorio=caminho_rel,
    )

    print("\n" + "=" * 60)
    print(" PIPELINE DE CLUSTERING EXECUTADO COM SUCESSO ")
    print("=" * 60)
    print(f"Identificador: {resultado.identificador}")
    print(f"Registros processados: {resultado.total_registros_processados}")
    print(f"Algoritmo: {conf.clustering.clustering.algoritmo}")
    print(f"Quantidade de clusters: {resultado.metricas.quantidade_clusters}")
    print(f"Pontos ruído (-1): {resultado.metricas.quantidade_pontos_ruido}")
    if resultado.metricas.silhouette_score is not None:
        print(f"Silhouette Score: {resultado.metricas.silhouette_score:.4f}")
    if resultado.metricas.davies_bouldin_index is not None:
        print(f"Davies-Bouldin Index: {resultado.metricas.davies_bouldin_index:.4f}")
    if resultado.run_id_mlflow:
        print(f"Run ID MLflow: {resultado.run_id_mlflow}")
    print(f"Relatório HTML interativo salvo em: {resultado.caminho_relatorio_html}")
    print("=" * 60 + "\n")


def iniciar_servidor_api(host: str, porta: int, recarregar: bool) -> None:
    """Inicia o servidor REST FastAPI com Uvicorn."""
    diretorio_config = Path("config")
    print(f"[*] Carregando configurações da API de '{diretorio_config}'...")
    conf = ConfYAML.carregar_de_diretorio(diretorio_config)

    repositorio = RepositorioS3Lakehouse(config=conf.datalake.datalake)
    estado = EstadoAplicacao(
        config_api=conf.api.api,
        config_clustering=conf.clustering.clustering,
        repositorio=repositorio,
        nomes_atributos=conf.atributos.atributos.treino.colunas,
    )

    app = criar_aplicacao_fastapi(estado)
    print(f"[*] Iniciando servidor API em http://{host}:{porta} ...")
    uvicorn.run(app, host=host, port=porta, reload=recarregar)


def main() -> None:
    """Roteamento dos comandos CLI."""
    parser = argparse.ArgumentParser(
        description="Plataforma de Clustering de Avaliações (Steam / Lakehouse S3 / MLflow)",
    )
    subparsers = parser.add_subparsers(dest="comando", help="Comando a ser executado")

    # Subcomando pipeline
    parser_pipe = subparsers.add_parser("pipeline", help="Executa o pipeline completo de clustering")
    parser_pipe.add_argument(
        "--identificador",
        "-i",
        default="730",
        help="Identificador do jogo ou recurso (padrão: 730 - Counter-Strike)",
    )
    parser_pipe.add_argument(
        "--coletar",
        "-c",
        action="store_true",
        help="Executa coleta de novos dados diretamente da fonte antes de processar",
    )
    parser_pipe.add_argument(
        "--relatorio",
        "-r",
        default="relatorio_clusters.html",
        help="Caminho para exportação do relatório HTML Plotly",
    )

    # Subcomando api
    parser_api = subparsers.add_parser("api", help="Inicia a API REST FastAPI")
    parser_api.add_argument("--host", default="0.0.0.0", help="Host de ligação (padrão: 0.0.0.0)")
    parser_api.add_argument("--porta", "-p", type=int, default=8000, help="Porta de escuta (padrão: 8000)")
    parser_api.add_argument("--reload", action="store_true", help="Habilita auto-reload para desenvolvimento")

    args = parser.parse_args()

    if args.comando == "pipeline":
        executar_pipeline_cli(
            identificador=args.identificador,
            coletar=args.coletar,
            caminho_relatorio=args.relatorio,
        )
    elif args.comando == "api":
        iniciar_servidor_api(
            host=args.host,
            porta=args.porta,
            recarregar=args.reload,
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
