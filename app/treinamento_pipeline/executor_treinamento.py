"""Orquestrador do ciclo completo de treinamento, pré-processamento, clustering, MLOps e avaliação."""

from typing import final

import pandas as pd

from app.agrupamento_modelos.capacidades_algoritmo import EstrategiaAgrupamento
from app.agrupamento_modelos.fabrica_agrupadores import FabricaAgrupadores
from app.avaliacao_modelos.avaliador_clusters import AvaliadorClusters
from app.avaliacao_modelos.metricas_estatisticas import ResultadoAvaliacao
from app.configuracao_geral.conf_yaml import ConfYAML
from app.engenharia_atributos.gerador_atributos import GeradorAtributosDerivados
from app.engenharia_atributos.seletor_colunas import SeletorColunasTreinamento
from app.integracao_mlflow.observador_nulo import ObservadorNulo
from app.integracao_mlflow.observador_treinamento import ObservadorTreinamento
from app.integracao_mlflow.registro_modelos import RegistroModelos
from app.preprocessamento_ml.fabrica_preprocessamento import (
    FabricaPreprocessamento,
)
from app.preprocessamento_ml.pipeline_composto import PipelineComposto
from app.regras_negocio.rotulador_clusters import RotuladorClusters
from app.visualizacao_dados.painel_executivo import PainelExecutivo


@final
class ExecutorTreinamento:
    """Orquestra a transformação analítica, pré-processamento, modelagem, telemetria MLOps e avaliação Gold."""

    def __init__(
        self,
        configuracoes: ConfYAML,
        gerador_atributos: GeradorAtributosDerivados | None = None,
        seletor_colunas: SeletorColunasTreinamento | None = None,
        fabrica_preprocessamento: FabricaPreprocessamento | None = None,
        fabrica_agrupadores: FabricaAgrupadores | None = None,
        avaliador: AvaliadorClusters | None = None,
        observador_mlops: ObservadorTreinamento | None = None,
        registro_modelos: RegistroModelos | None = None,
        rotulador_negocio: RotuladorClusters | None = None,
        painel_executivo: PainelExecutivo | None = None,
    ) -> None:
        self._config = configuracoes
        self._gerador = gerador_atributos or GeradorAtributosDerivados()
        self._seletor = seletor_colunas or SeletorColunasTreinamento()
        self._fabrica_pre = fabrica_preprocessamento or FabricaPreprocessamento()
        self._fabrica_agrupadores = fabrica_agrupadores or FabricaAgrupadores()
        self._avaliador = avaliador or AvaliadorClusters()
        self._observador = observador_mlops or ObservadorNulo()
        self._registro = registro_modelos or RegistroModelos()
        self._rotulador = rotulador_negocio
        self._painel = painel_executivo or PainelExecutivo()

    def executar_treinamento(
        self,
        dados_silver: pd.DataFrame,
        nome_algoritmo: str = "kmeans",
        parametros_algoritmo: dict[str, object] | None = None,
        versao_dataset: str = "gold_v1",
    ) -> tuple[pd.DataFrame, ResultadoAvaliacao, EstrategiaAgrupamento]:
        """Aplica engenharia de atributos, pré-processamento, treina agrupador, avalia e notifica MLOps."""
        if dados_silver.empty:
            raise ValueError("Não é possível treinar modelos em um DataFrame vazio.")

        params = parametros_algoritmo or {}

        # 1. Notifica início no Observer
        self._observador.registrar_inicio(
            nome_experimento=self._config.projeto.configuracao.nome_projeto,
            nome_execucao=f"{nome_algoritmo}_{versao_dataset}",
            parametros=params,
            tags={
                "algoritmo": nome_algoritmo,
                "versao_dataset": versao_dataset,
                "hash_config": self._config.hash_configuracao,
            },
        )

        try:
            # 2. Engenharia de atributos analíticos
            dados_enriquecidos = self._gerador.calcular_atributos(dados_silver)

            # 3. Seleção de atributos de treino conforme configuração
            colunas_treino = [
                "num_reviews",
                "playtime_forever",
                "playtime_last_two_weeks",
                "playtime_at_review",
                "dias_desde_ultima_atividade",
            ]
            matriz_x = self._seletor.extrair_matriz_treino(
                dados_enriquecidos, colunas_treino
            )

            # 4. Montagem e ajuste do pipeline de pré-processamento
            pipeline_pre: PipelineComposto = self._fabrica_pre.construir_pipeline(
                imputacao_ativada=True,
                tecnica_imputacao="median",
                escalonamento_ativado=True,
                tecnica_escalonamento="standard_scaler",
                reducao_ativada=False,
            )
            x_processado = pipeline_pre.ajustar_e_transformar(matriz_x.to_numpy())

            # 5. Instanciação e treinamento do agrupador
            agrupador = self._fabrica_agrupadores.criar_agrupador(
                nome_algoritmo=nome_algoritmo,
                parametros=params,
            )
            rotulos = agrupador.treinar(x_processado)

            # 6. Avaliação estatística
            resultado_avaliacao = self._avaliador.avaliar(x_processado, rotulos)

            # 7. Composição do dataset Gold
            dados_gold = dados_enriquecidos.copy()
            dados_gold["cluster_id"] = rotulos
            dados_gold["cluster_label"] = rotulos

            # 8. Rotulagem semântica de negócio (se ativada)
            mapa_rotulos: dict[int, str] = {}
            if self._rotulador is not None:
                dados_gold, mapa_rotulos = self._rotulador.rotular_clusters(dados_gold)

            # 9. Notificação de Métricas e Distribuição ao Observer
            metricas_dict: dict[str, float] = {
                "total_amostras": float(resultado_avaliacao.total_amostras),
                "total_clusters": float(resultado_avaliacao.total_clusters),
                "proporcao_ruido": float(resultado_avaliacao.proporcao_ruido),
            }
            if resultado_avaliacao.silhouette_global is not None:
                metricas_dict["silhouette_global"] = (
                    resultado_avaliacao.silhouette_global
                )
            if resultado_avaliacao.silhouette_sem_ruido is not None:
                metricas_dict["silhouette_sem_ruido"] = (
                    resultado_avaliacao.silhouette_sem_ruido
                )
            if resultado_avaliacao.davies_bouldin is not None:
                metricas_dict["davies_bouldin"] = resultado_avaliacao.davies_bouldin
            if resultado_avaliacao.calinski_harabasz is not None:
                metricas_dict["calinski_harabasz"] = (
                    resultado_avaliacao.calinski_harabasz
                )

            self._observador.registrar_metricas(metricas_dict)
            self._observador.registrar_distribuicao_clusters(rotulos)

            # 10. Persistência de artefatos do modelo via RegistroModelos
            self._registro.registrar_pipeline_completo(
                pipeline=pipeline_pre,
                algoritmo=agrupador,
                nomes_colunas_treino=colunas_treino,
                versao_dataset=versao_dataset,
                hash_configuracao=self._config.hash_configuracao,
            )

            # 11. Relatório executivo de resumo
            relatorio_md = self._painel.compilar_relatorio_markdown(
                metricas=resultado_avaliacao,
                nome_algoritmo=nome_algoritmo,
                mapa_rotulos_negocio=mapa_rotulos,
                dados_gold=dados_gold,
            )
            self._observador.registrar_artefato_texto(
                relatorio_md, "relatorio_executivo.md"
            )

            self._observador.registrar_fim(status="FINISHED")

            return dados_gold, resultado_avaliacao, agrupador

        except Exception:
            self._observador.registrar_fim(status="FAILED")
            raise
