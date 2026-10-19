"""Ponto de entrada executável para disparo do ExecutorCiclo via CLI ou agendador."""

import argparse
import os
from pathlib import Path
import sys

from app.analise_tendencias.agregador_visoes import AgregadorVisoes
from app.analise_tendencias.calculador_tendencias import CalculadorTendencias
from app.coleta_youtube.cliente_youtube import ClienteYouTube
from app.coleta_youtube.extrator_comentarios import ExtratorComentarios
from app.configuracao_geral.provedor_configuracao import ProvedorConfiguracao
from app.gestao_dados.camada_bronze import CamadaBronze
from app.gestao_dados.camada_ouro import CamadaOuro
from app.gestao_dados.camada_prata import CamadaPrata
from app.gestao_dados.cliente_s3 import ClienteS3
from app.integracao_mlflow.rastreador_experimentos import RastreadorExperimentos
from app.orquestracao_pipeline.executor_ciclo import ExecutorCiclo
from app.tratamento_texto.lematizador_spacy import LematizadorSpacy
from app.tratamento_texto.rotulador_topicos import RotuladorTopicos


def main() -> int:
    """Executa o ciclo diário do pipeline para canais informados ou configurados."""
    parser = argparse.ArgumentParser(
        description="Disparador do ciclo de coleta, processamento, ML e lakehouse de comentários do YouTube."
    )
    parser.add_argument(
        "--canal",
        "-c",
        type=str,
        default=None,
        help="ID do canal do YouTube para processamento individual.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/entradas.yaml",
        help="Caminho do arquivo de configuração YAML.",
    )

    args = parser.parse_args()

    caminho_config = Path(args.config)
    if not caminho_config.exists():
        print(f"[ERRO] Arquivo de configuração não encontrado: {caminho_config}", file=sys.stderr)
        return 1

    caminho_env = Path(".env")
    if caminho_env.exists():
        for linha in caminho_env.read_text(encoding="utf-8").splitlines():
            linha_limpa = linha.strip()
            if linha_limpa and not linha_limpa.startswith("#") and "=" in linha_limpa:
                chave_env, _, valor_env = linha_limpa.partition("=")
                os.environ.setdefault(chave_env.strip(), valor_env.strip())

    config = ProvedorConfiguracao(caminho_config).carregar()

    chave_api = os.getenv(config.coleta.chave_api_env, "")
    endpoint_s3 = os.getenv(config.persistencia.endpoint_env, "http://127.0.0.1:9000")
    access_key = os.getenv(config.persistencia.access_key_env, "s3admin")
    secret_key = os.getenv(config.persistencia.secret_key_env, "s3admin")
    tracking_uri = os.getenv(config.mlflow.tracking_uri_env, "http://127.0.0.1:5000")

    # Resolução dos canais a processar
    canais_alvo: list[str] = []
    if args.canal:
        canais_alvo.append(args.canal.strip())
    else:
        for canal_item in config.coleta.canais:
            if canal_item.ativo:
                canais_alvo.append(canal_item.id_canal.strip())

    if not canais_alvo:
        print(
            "[AVISO] Nenhum canal ativo configurado em config/entradas.yaml nem informado via --canal.",
            file=sys.stderr,
        )
        print("Uso: ./scripts/executar_ciclo.sh <ID_DO_CANAL>", file=sys.stderr)
        return 1

    print("=================================================================")
    print(" INICIALIZANDO DISPARO DO EXECUTOR DE CICLO DIÁRIO")
    print("=================================================================")
    print(f"• Configuração: {caminho_config}")
    print(f"• Endpoint S3:  {endpoint_s3}")
    print(f"• Bucket S3:    {config.persistencia.bucket}")
    print(f"• MLflow URI:   {tracking_uri}")
    print(f"• Canais alvo:  {canais_alvo}")
    print("-----------------------------------------------------------------")

    cliente_yt = ClienteYouTube(chave_api=chave_api or "MOCK_KEY_LOCAL")
    extrator = ExtratorComentarios(cliente_yt)
    s3 = ClienteS3(
        endpoint_url=endpoint_s3,
        access_key=access_key,
        secret_key=secret_key,
    )
    bronze = CamadaBronze(
        s3,
        bucket=config.persistencia.bucket,
        prefixo_bronze=config.persistencia.prefixo_bronze,
        padrao_chave=config.persistencia.padrao_chave_bronze,
    )
    prata = CamadaPrata(
        s3,
        bucket=config.persistencia.bucket,
        prefixo_prata=config.persistencia.prefixo_prata,
        padrao_chave=config.persistencia.padrao_chave_prata,
    )
    ouro = CamadaOuro(
        s3,
        bucket=config.persistencia.bucket,
        prefixo_ouro=config.persistencia.prefixo_ouro,
        padrao_chave_video=config.persistencia.padrao_chave_ouro_video,
        padrao_chave_consolidado=config.persistencia.padrao_chave_ouro_consolidado,
    )

    lematizador = LematizadorSpacy(
        modelo_nome=config.processamento.spacy_modelo,
        preservar_negacoes=config.processamento.stopwords.preservar,
    )
    rotulador = RotuladorTopicos(
        peso_tfidf=config.topicos.peso_tfidf,
        peso_frequencia=config.topicos.peso_frequencia,
        penalizacao_global=config.topicos.penalizacao_global,
        comprimento_minimo=config.topicos.comprimento_minimo,
        limiar_penalizacao_global=config.topicos.limiar_penalizacao_global,
        fator_penalidade=config.topicos.fator_penalidade,
        rotulo_ruido_padrao=config.topicos.rotulo_ruido_padrao,
    )
    calculador = CalculadorTendencias(
        max_amostras_video=config.tendencias.max_amostras_video,
    )
    agregador = AgregadorVisoes(
        max_amostras_canal=config.tendencias.max_amostras_canal,
    )
    rastreador = RastreadorExperimentos(
        tracking_uri=tracking_uri,
    )

    executor = ExecutorCiclo(
        config=config,
        extrator=extrator,
        bronze=bronze,
        prata=prata,
        ouro=ouro,
        lematizador=lematizador,
        rotulador=rotulador,
        calculador_tendencias=calculador,
        agregador_visoes=agregador,
        rastreador_mlflow=rastreador,
    )

    for id_canal in canais_alvo:
        print(f"\n[EXECUÇÃO] Disparando ciclo para o canal: {id_canal}...")
        try:
            resultado = executor.executar_ciclo_canal(id_canal)
            print(f"[SUCESSO] Canal {id_canal} processado com sucesso!")
            print(f"          - Vídeos processados:     {resultado.get('videos', 0)}")
            print(f"          - Comentários coletados:  {resultado.get('comentarios', 0)}")
            print(f"          - Tópicos na Camada Ouro: {resultado.get('topicos_ouro', 0)}")
        except Exception as erro:
            print(f"[FALHA] Erro durante processamento do canal {id_canal}: {erro}", file=sys.stderr)
            return 2

    print("\n=================================================================")
    print(" CICLO FINALIZADO COM SUCESSO")
    print("=================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
