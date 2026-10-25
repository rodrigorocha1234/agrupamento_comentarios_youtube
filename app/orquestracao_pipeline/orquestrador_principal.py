"""Orquestrador principal de ponta a ponta do projeto Steam Reviews Clustering v4.1."""

import argparse
import io
import logging
import os
import sys
from typing import final

import numpy as np
import pandas as pd
from botocore.exceptions import ClientError

from app.agrupamento_modelos.selecionador_automl import SelecionadorModelosAutoML
from app.configuracao_geral.conf_yaml import ConfYAML
from app.dominio_contratos.modelos_dados import TipoParametroAlgoritmo
from app.dominio_contratos.protocolos_datalake import ArmazenamentoLake
from app.engenharia_atributos.gerador_atributos import GeradorAtributosDerivados
from app.engenharia_atributos.seletor_colunas import SeletorColunasTreinamento
from app.extracao_steam.fabrica_extracao import FabricaExtracao
from app.gestao_datalake.cliente_rustfs import ClienteRustfsS3
from app.gestao_datalake.despachante_outbox import DespachanteOutbox
from app.gestao_datalake.escritor_ouro import EscritorCamadaOuro
from app.gestao_datalake.escritor_prata import EscritorCamadaPrata
from app.observabilidade_metricas.telemetria_analitica import TelemetriaAnalitica
from app.orquestracao_pipeline.executor_coleta import ExecutorColetaStaging
from app.persistencia_staging.fabrica_staging import FabricaStaging
from app.regras_negocio.rotulador_clusters import RotuladorClusters
from app.treinamento_pipeline.executor_treinamento import ExecutorTreinamento
from app.treinamento_pipeline.exportador_ouro import ExportadorCamadaOuro

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("orquestrador_principal")


@final
class OrquestradorPrincipal:
    """Coordena a execução integrada de coleta, staging, lakehouse e modelagem analítica."""

    def __init__(
        self,
        configuracoes: ConfYAML | None = None,
        fabrica_staging: FabricaStaging | None = None,
        fabrica_extracao: FabricaExtracao | None = None,
        armazenamento_lake: ArmazenamentoLake | None = None,
    ) -> None:
        self._config = configuracoes or ConfYAML()
        self._fabrica_staging = fabrica_staging or FabricaStaging()
        self._fabrica_extracao = fabrica_extracao or FabricaExtracao()
        self._armazenamento = armazenamento_lake

    def executar_fluxo_coleta(
        self,
        appid: int,
        tipo_banco: str = "auto",
        tipo_api: str = "web_api",
        estrategia: str = "recente",
        limite_paginas: int = 2,
    ) -> None:
        """Executa a coleta paginada da Steam API com staging transacional e outbox."""
        logger.info(
            "Iniciando ciclo de coleta da Steam API para AppID: %d (estratégia: %s)",
            appid,
            estrategia,
        )

        banco_resolvido = tipo_banco
        if banco_resolvido == "auto":
            banco_resolvido = (
                "postgres"
                if "postgresql" in os.getenv("DATABASE_URL", "")
                else "sqlite"
            )

        logger.info(
            "Resolvendo persistência relacional de staging via FabricaStaging: %s",
            banco_resolvido,
        )
        uow, repo = self._fabrica_staging.criar_staging(banco_resolvido)

        logger.info(
            "Instanciando gerador de extração desacoplado via FabricaExtracao: provedor '%s'",
            tipo_api,
        )
        gerador = self._fabrica_extracao.criar_gerador(
            nome_provedor=tipo_api,
            limite_paginas=limite_paginas,
        )

        storage = self._armazenamento or ClienteRustfsS3()
        despachante = DespachanteOutbox(
            repositorio=repo, armazenamento=storage
        )
        escritor_prata = EscritorCamadaPrata(armazenamento=storage)

        executor = ExecutorColetaStaging(
            configuracoes=self._config,
            gerador_paginas=gerador,
            uow=uow,
            repositorio=repo,
            despachante_outbox=despachante,
            escritor_prata=escritor_prata,
        )

        try:
            resultado = executor.executar_coleta_jogo(
                appid=appid, estrategia=estrategia
            )
            logger.info(
                "Coleta concluída! ID Execução: %s | Páginas: %d | Reviews: %d | Status: %s",
                resultado.id_execucao,
                resultado.total_paginas,
                resultado.total_reviews,
                resultado.status,
            )
        except (OSError, RuntimeError, ValueError) as erro:
            logger.warning(
                "Aviso de coleta Steam (possível falta de rede externa ou rate limit): %s. Prosseguindo com dados locais.",
                erro,
            )

    def executar_fluxo_treinamento(
        self,
        appid: int,
        algoritmo: str = "automl",
        versao_dataset: str = "gold_v4_1",
    ) -> None:
        """Executa engenharia de atributos, clustering AutoML, rotulagem declarativa e exportação Gold."""
        logger.info(
            "Iniciando pipeline analítico e de machine learning para AppID: %d",
            appid,
        )

        dados_treino = self.obter_dados_silver(appid)
        logger.info(
            "Dataset base carregado com %d observações para modelagem.",
            len(dados_treino),
        )

        algoritmo_campeao = algoritmo
        parametros_campeao: dict[str, TipoParametroAlgoritmo] = {}

        if algoritmo.lower() == "automl":
            logger.info(
                "Executando seleção de modelos AutoML orientada a capacidades..."
            )
            gerador = GeradorAtributosDerivados()
            dados_enriquecidos = gerador.calcular_atributos(dados_treino)
            seletor = SeletorColunasTreinamento()
            colunas_candidatas = [
                "num_reviews",
                "playtime_forever",
                "playtime_last_two_weeks",
                "playtime_at_review",
                "dias_desde_ultima_atividade",
                "comment_count",
            ]
            matriz_df = seletor.extrair_matriz_treino(
                dados_enriquecidos, colunas_candidatas
            )
            matriz_x = np.asarray(matriz_df.to_numpy(), dtype=np.float64)

            selecionador = SelecionadorModelosAutoML()
            _modelo_opt, _avaliacao_opt, melhor_algoritmo, melhor_score = (
                selecionador.selecionar_melhor_modelo(matriz_x)
            )
            algoritmo_campeao = melhor_algoritmo or "kmeans"
            logger.info(
                "AutoML selecionou o algoritmo: %s com score balanceado: %.4f",
                algoritmo_campeao,
                melhor_score,
            )
        else:
            if algoritmo_campeao == "kmeans":
                parametros_campeao = {"n_clusters": 4}
            elif algoritmo_campeao == "dbscan":
                parametros_campeao = {"eps": 0.5, "min_samples": 5}
            elif algoritmo_campeao == "hdbscan":
                parametros_campeao = {"min_cluster_size": 10}

        rotulador = RotuladorClusters()
        executor = ExecutorTreinamento(
            configuracoes=self._config, rotulador_negocio=rotulador
        )

        df_rotulado, avaliacao, _modelo = executor.executar_treinamento(
            dados_silver=dados_treino,
            nome_algoritmo=algoritmo_campeao,
            parametros_algoritmo=parametros_campeao,
            versao_dataset=versao_dataset,
        )

        logger.info(
            "Treinamento e rotulagem finalizados com sucesso! Clusters formados: %d | Silhueta: %.4f",
            avaliacao.total_clusters,
            avaliacao.silhouette_global or 0.0,
        )

        storage = self._armazenamento or ClienteRustfsS3()
        escritor_ouro = EscritorCamadaOuro(armazenamento=storage)
        telemetria = TelemetriaAnalitica()
        exportador = ExportadorCamadaOuro(
            escritor_ouro=escritor_ouro,
            telemetria_analitica=telemetria,
        )

        try:
            manifesto = exportador.exportar_camada_ouro(
                appid=appid,
                nome_algoritmo=algoritmo_campeao,
                versao=versao_dataset,
                dados_gold=df_rotulado,
                avaliacao=avaliacao,
                hash_execucao=self._config.hash_configuracao,
            )
            logger.info(
                "Camada Gold materializada no Lakehouse com manifesto: %s",
                manifesto.get("manifesto", "ok"),
            )
        except (OSError, RuntimeError, ValueError) as erro:
            logger.warning(
                "Aviso ao persistir no Lakehouse S3 (possível container storage offline): %s",
                erro,
            )

    def obter_dados_silver(self, appid: int) -> pd.DataFrame:
        """Carrega os dados normalizados da camada Silver gravados no bucket S3 ou Lakehouse."""
        logger.info(
            "Recuperando dados da camada Silver para AppID %d do bucket Lakehouse...",
            appid,
        )
        storage = self._armazenamento or ClienteRustfsS3()
        prefixo_silver = f"silver/steam/reviews/appid={appid}/"

        nome_bucket = getattr(storage, "bucket", "steam-reviews")

        # 1. Busca objetos Parquet persistidos no bucket S3/RustFS
        try:
            chaves = [
                chave
                for chave in storage.listar_chaves(prefixo_silver)
                if chave.endswith(".parquet")
            ]
            if chaves:
                logger.info(
                    "Encontrados %d arquivos Parquet no bucket '%s' sob o prefixo '%s'.",
                    len(chaves),
                    nome_bucket,
                    prefixo_silver,
                )
                dfs: list[pd.DataFrame] = []
                for chave in chaves:
                    conteudo = storage.ler_bytes(chave)
                    df_lote = pd.read_parquet(io.BytesIO(conteudo))
                    dfs.append(df_lote)
                if dfs:
                    df_consolidado = pd.concat(dfs, ignore_index=True)
                    logger.info(
                        "Carregados com sucesso %d registros da camada Silver a partir do bucket.",
                        len(df_consolidado),
                    )
                    return df_consolidado
        except (ClientError, OSError, ValueError) as erro:
            logger.warning(
                "Aviso ao consultar partição Silver no bucket S3 (%s). Verificando caminho local do Lakehouse.",
                erro,
            )

        # 2. Verifica se a partição Silver existe no caminho de armazenamento local
        caminho_local_silver = f"lakehouse/silver/steam/reviews/appid={appid}"
        if os.path.exists(caminho_local_silver):
            try:
                df_local = pd.read_parquet(caminho_local_silver)
                logger.info(
                    "Carregados com sucesso %d registros do caminho local '%s'.",
                    len(df_local),
                    caminho_local_silver,
                )
                return df_local
            except (OSError, ValueError) as erro:
                logger.warning(
                    "Falha ao ler Parquet local da camada Silver (%s).", erro
                )

        # 3. Eliminação de dados sintéticos: lança exceção explícita se os dados não existirem
        raise FileNotFoundError(
            f"Nenhum dado encontrado na partição Silver para o AppID {appid} no bucket "
            f"'{nome_bucket}' (prefixo '{prefixo_silver}') nem no caminho local '{caminho_local_silver}'. "
            "Execute previamente a etapa de coleta e staging para que os dados reais sejam gravados no bucket."
        )

    def _obter_dados_silver(self, appid: int) -> pd.DataFrame:
        """Alias legado protegido."""
        return self.obter_dados_silver(appid)

    def _obter_dados_silver_ou_sinteticos(self, appid: int) -> pd.DataFrame:
        """Alias mantido para compatibilidade, direcionando para a leitura exclusiva do bucket."""
        return self.obter_dados_silver(appid)


def main() -> None:
    """Ponto de entrada de linha de comando para orquestração."""
    parser = argparse.ArgumentParser(
        description="Orquestrador Principal do Steam Reviews Clustering v4.1"
    )
    parser.add_argument(
        "--acao",
        type=str,
        choices=["coleta", "treinar", "tudo"],
        default="tudo",
        help="Ação a ser executada pelo pipeline",
    )
    parser.add_argument(
        "--appid",
        type=int,
        default=427520,
        help="Identificador do jogo na Steam (padrão: 427520)",
    )
    parser.add_argument(
        "--banco",
        type=str,
        choices=["auto", "postgres", "sqlite"],
        default="auto",
        help="Mecanismo de staging relacional",
    )
    parser.add_argument(
        "--tipo-api",
        type=str,
        default="web_api",
        help="Provedor ou cliente de extração da Steam (padrão: web_api)",
    )
    parser.add_argument(
        "--algoritmo",
        type=str,
        default="automl",
        help="Algoritmo de clustering (automl, kmeans, dbscan, hdbscan)",
    )
    parser.add_argument(
        "--max-paginas",
        type=int,
        default=2,
        help="Limite máximo de páginas para a coleta",
    )

    args = parser.parse_args()

    orquestrador = OrquestradorPrincipal()

    try:
        if args.acao in ("coleta", "tudo"):
            orquestrador.executar_fluxo_coleta(
                appid=args.appid,
                tipo_banco=args.banco,
                tipo_api=args.tipo_api,
                limite_paginas=args.max_paginas,
            )

        if args.acao in ("treinar", "tudo"):
            orquestrador.executar_fluxo_treinamento(
                appid=args.appid,
                algoritmo=args.algoritmo,
            )

        logger.info("Execução finalizada com êxito!")

    except Exception:
        logger.exception("Falha durante a orquestração do pipeline.")
        sys.exit(1)


if __name__ == "__main__":
    main()
