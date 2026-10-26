"""Fachada unificada (Facade) para orquestração ponta a ponta do pipeline de clustering."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import plotly.graph_objects as go

from app.analise_clusters.analisador_clusters import (
    AnalisadorClusters,
    ResumoAnaliseClusters,
)
from app.analise_clusters.gerador_graficos import GeradorVisualizacoesClusters
from app.analise_temporal import FabricaAnaliseTemporal, ResumoAnaliseTemporal
from app.clustering.avaliador_clusters import MetricasClustering
from app.clustering.executor_clustering import ExecutorClustering, ResultadoClustering
from app.clustering.rastreador_mlflow import RastreadorMLflow
from app.conf_yaml import (
    ConfigAnalisesInfo,
    ConfigAnaliseTemporalInfo,
    ConfigAtributosInfo,
    ConfigClusteringInfo,
    ConfigFonteDados,
    ConfigFonteInfo,
    ConfigMLflowInfo,
    ConfigPLNInfo,
    ConfigPreprocessamentoInfo,
    ConfigProcessamentoInfo,
    ConfigRegrasNegocioInfo,
)
from app.contratos.fonte_dados import ProtocoloFonteDados
from app.contratos.repositorio import ProtocoloRepositorioLakehouse
from app.gestao_datalake.repositorio_s3_lakehouse import RepositorioS3Lakehouse
from app.ingestao_fontes.coletor_dados import ColetorDados
from app.ingestao_fontes.fabrica_fontes import FabricaFontesDados
from app.preprocessamento_ml.engenheiro_atributos import EngenheiroAtributos
from app.processamento_dados.processador_tabela import ProcessadorTabela
from app.processamento_pln.fachada_pln import FachadaProcessamentoPLN
from app.regras_negocio.avaliador_regras import AvaliadorRegrasNegocio

SUFIXO_VISAO_CLUSTERS: Final[str] = "clusters"


@dataclass(frozen=True)
class ResultadoExecucaoPipeline:
    """Consolida as saídas de todas as etapas executadas do pipeline."""

    identificador: str | int
    sucesso: bool
    total_registros_processados: int
    resultado_clustering: ResultadoClustering
    resumo_analitico: ResumoAnaliseClusters
    metricas: MetricasClustering
    figuras_geradas: dict[str, go.Figure] = field(default_factory=dict)
    caminho_relatorio_html: str = ""
    run_id_mlflow: str | None = None
    resumo_temporal: ResumoAnaliseTemporal | None = None


class FachadaPipelineClustering:
    """Orquestrador unificado de ingestão, camadas lakehouse, ML e análises."""

    def __init__(
        self,
        config_fonte: ConfigFonteInfo,
        config_processamento: ConfigProcessamentoInfo,
        config_atributos: ConfigAtributosInfo,
        config_preprocessamento: ConfigPreprocessamentoInfo,
        config_clustering: ConfigClusteringInfo,
        config_mlflow: ConfigMLflowInfo | None = None,
        config_analises: ConfigAnalisesInfo | None = None,
        config_regras_negocio: ConfigRegrasNegocioInfo | None = None,
        config_pln: ConfigPLNInfo | None = None,
        config_analise_temporal: ConfigAnaliseTemporalInfo | None = None,
        repositorio_lakehouse: ProtocoloRepositorioLakehouse | None = None,
        fonte_dados: ProtocoloFonteDados | None = None,
    ) -> None:
        self._config_fonte = config_fonte
        self._config_processamento = config_processamento
        self._config_atributos = config_atributos
        self._config_preprocessamento = config_preprocessamento
        self._config_clustering = config_clustering
        self._config_mlflow = config_mlflow or ConfigMLflowInfo(habilitado=False)
        self._config_analises = config_analises or ConfigAnalisesInfo()
        self._config_regras_negocio = config_regras_negocio or ConfigRegrasNegocioInfo(habilitado=False)
        self._config_pln = config_pln or ConfigPLNInfo(habilitado=False)
        self._config_temporal = config_analise_temporal or ConfigAnaliseTemporalInfo(habilitado=False)

        self._repositorio = repositorio_lakehouse or RepositorioS3Lakehouse()
        self._fonte_dados = fonte_dados or FabricaFontesDados.criar_fonte(
            ConfigFonteDados(fonte=config_fonte)
        )
        self._rastreador_mlflow = RastreadorMLflow(self._config_mlflow)
        self._avaliador_regras = AvaliadorRegrasNegocio(self._config_regras_negocio)
        self._fachada_pln = FachadaProcessamentoPLN(self._config_pln)
        self._analisador_temporal = FabricaAnaliseTemporal.criar_analisador(self._config_temporal)

    def executar(
        self,
        identificador: str | int,
        coletar_dados_novos: bool = False,
        caminho_exportacao_relatorio: str | Path | None = None,
    ) -> ResultadoExecucaoPipeline:
        """Executa o ciclo completo de clustering no Lakehouse."""
        # 1. Coleta e Ingestão (opcional ou se solicitado)
        if coletar_dados_novos:
            coletor = ColetorDados(
                fonte=self._fonte_dados,
                repositorio=self._repositorio,
            )
            coletor.executar_coleta(
                identificador_origem=identificador,
            )

        # 2. Leitura da camada Bronze e Processamento para Silver
        dados_bronze = self._repositorio.ler_bronze(identificador)
        processador = ProcessadorTabela()
        dados_silver = processador.processar(dados_bronze, self._config_processamento)
        if self._avaliador_regras.habilitado:
            dados_silver = self._avaliador_regras.aplicar_regras_amostras(dados_silver)
        self._repositorio.gravar_silver(identificador, dados_silver)

        # 3. Engenharia de Atributos & Matriz Analítica Gold
        engenheiro = EngenheiroAtributos(self._config_atributos)
        artefato_gold = engenheiro.processar_e_persistir_gold(
            identificador=identificador,
            dados_silver=dados_silver,
            config_preprocessamento=self._config_preprocessamento,
            repositorio=self._repositorio,
        )

        # 3.1 Processamento e Fusão de PLN (quando habilitado)
        matriz_treino_final = artefato_gold.matriz_treino
        if self._fachada_pln.habilitado:
            matriz_treino_final = self._fachada_pln.processar_e_fundir(
                dados_silver=dados_silver,
                matriz_numerica_treino=matriz_treino_final,
            )

        # 4. Ajuste do Motor de Clustering & MLflow Tracking
        executor_clustering = ExecutorClustering(
            config_clustering=self._config_clustering,
            config_mlflow=self._config_mlflow,
            rastreador=self._rastreador_mlflow,
        )
        resultado_clustering = executor_clustering.executar(
            matriz_treino=matriz_treino_final,
            metadados=artefato_gold.metadados,
            identificador=identificador,
            repositorio=self._repositorio,
        )

        # 5. Análise de Perfis & Diagnósticos
        matriz_np = matriz_treino_final.to_numpy(dtype=float)
        centroides = resultado_clustering.motor.obter_centroides()
        resumo_analitico = AnalisadorClusters.gerar_resumo_estatistico(
            matriz_treino=matriz_treino_final,
            rotulos=resultado_clustering.rotulos,
            metadados=artefato_gold.metadados,
            centroides=centroides,
            avaliador_regras=self._avaliador_regras,
            config_analises=self._config_analises,
        )

        # 6. Geração de Gráficos e Relatório Plotly
        figuras: dict[str, go.Figure] = {}
        opcoes_visuais = self._config_analises.clusters

        if opcoes_visuais.resumo:
            figuras["resumo"] = GeradorVisualizacoesClusters.gerar_tabela_resumo_clusters(
                resumo=resumo_analitico,
                config_analises=self._config_analises,
            )

        if opcoes_visuais.distribuicao:
            figuras["distribuicao"] = GeradorVisualizacoesClusters.gerar_grafico_distribuicao_clusters(
                rotulos=resultado_clustering.rotulos,
                config_analises=self._config_analises,
            )

        if opcoes_visuais.dispersao_2d and len(artefato_gold.nomes_atributos) >= 2:
            cfg_disp = self._config_analises.dispersao
            attr_x = cfg_disp.atributo_x if cfg_disp.atributo_x in artefato_gold.matriz_treino.columns else artefato_gold.nomes_atributos[0]
            attr_y = cfg_disp.atributo_y if cfg_disp.atributo_y in artefato_gold.matriz_treino.columns else artefato_gold.nomes_atributos[1]

            figuras["dispersao_2d"] = GeradorVisualizacoesClusters.gerar_grafico_dispersao_2_atributos(
                dados=artefato_gold.matriz_treino,
                atributo_x=attr_x,
                atributo_y=attr_y,
                rotulos=resultado_clustering.rotulos,
                config_analises=self._config_analises,
            )

        if opcoes_visuais.perfil:
            figuras["perfil"] = GeradorVisualizacoesClusters.gerar_grafico_perfil_clusters(
                resumo=resumo_analitico,
                config_analises=self._config_analises,
            )

        if opcoes_visuais.pca_2d:
            figuras["pca_2d"] = GeradorVisualizacoesClusters.gerar_grafico_pca_2d(
                matriz_treino=matriz_np,
                rotulos=resultado_clustering.rotulos,
                config_analises=self._config_analises,
            )

        if opcoes_visuais.boxplot and artefato_gold.nomes_atributos:
            cfg_box = self._config_analises.boxplot
            attr_box = cfg_box.atributo if cfg_box.atributo in artefato_gold.matriz_treino.columns else artefato_gold.nomes_atributos[0]

            figuras["boxplot"] = GeradorVisualizacoesClusters.gerar_boxplot_atributos(
                dados=artefato_gold.matriz_treino,
                atributo=attr_box,
                rotulos=resultado_clustering.rotulos,
                config_analises=self._config_analises,
            )

        # 6.1 Análise Temporal dos Agrupamentos (quando habilitada)
        resumo_temporal: ResumoAnaliseTemporal | None = None
        if self._config_temporal.habilitado:
            resumo_temporal = self._analisador_temporal.analisar(
                dados=dados_silver,
                rotulos=resultado_clustering.rotulos,
            )
            if self._config_temporal.visualizacoes.grafico_evolucao_linhas and resumo_temporal.periodos_ordenados:
                figuras["evolucao_temporal"] = GeradorVisualizacoesClusters.gerar_grafico_evolucao_temporal(
                    resumo_temporal=resumo_temporal,
                    titulo=self._config_temporal.visualizacoes.titulo_evolucao,
                    config_analises=self._config_analises,
                )
            if self._config_temporal.visualizacoes.grafico_area_empilhada and resumo_temporal.periodos_ordenados:
                figuras["area_empilhada_temporal"] = GeradorVisualizacoesClusters.gerar_grafico_area_empilhada_temporal(
                    resumo_temporal=resumo_temporal,
                    titulo=self._config_temporal.visualizacoes.titulo_area_empilhada,
                    config_analises=self._config_analises,
                )

        caminho_relatorio_str = ""
        if caminho_exportacao_relatorio is not None and figuras:
            caminho_path = Path(caminho_exportacao_relatorio)
            GeradorVisualizacoesClusters.exportar_relatorio_html(
                figuras=list(figuras.values()),
                caminho_saida=caminho_path,
                config_analises=self._config_analises,
            )
            caminho_relatorio_str = str(caminho_path)

            # Registra como artefato no MLflow se habilitado
            if self._config_mlflow.habilitado:
                self._rastreador_mlflow.registrar_artefato(
                    caminho_local=caminho_relatorio_str,
                    subpasta_destino="relatorios_analiticos",
                )

        return ResultadoExecucaoPipeline(
            identificador=identificador,
            sucesso=True,
            total_registros_processados=len(dados_silver),
            resultado_clustering=resultado_clustering,
            resumo_analitico=resumo_analitico,
            metricas=resultado_clustering.metricas,
            figuras_geradas=figuras,
            caminho_relatorio_html=caminho_relatorio_str,
            run_id_mlflow=resultado_clustering.run_id,
            resumo_temporal=resumo_temporal,
        )
