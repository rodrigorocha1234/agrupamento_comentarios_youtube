"""Orquestrador sequencial do pipeline diário fim-a-fim."""

import time

from app.agrupamento_modelos.fabrica_agrupadores import FabricaAgrupadores
from app.analise_tendencias.agregador_visoes import AgregadorVisoes
from app.analise_tendencias.calculador_tendencias import CalculadorTendencias
from app.coleta_metricas.medidor_coleta import (
    HISTOGRAMA_ETAPAS_PIPELINE,
    MedidorColeta,
)
from app.coleta_metricas.medidor_modelos import MedidorModelos
from app.coleta_youtube.extrator_comentarios import ExtratorComentarios
from app.configuracao_geral.modelos_configuracao import ConfiguracaoGlobal
from app.gestao_dados.camada_bronze import CamadaBronze
from app.gestao_dados.camada_ouro import CamadaOuro, RegistroTopicoOuro
from app.gestao_dados.camada_prata import CamadaPrata
from app.integracao_mlflow.rastreador_experimentos import (
    RastreadorExperimentos,
)
from app.orquestracao_pipeline.despachante_alertas import DespachanteAlertas
from app.orquestracao_pipeline.protocolos_ciclo import (
    ProtocoloAgregadorVisoes,
    ProtocoloCalculadorTendencias,
    ProtocoloCamadaBronze,
    ProtocoloCamadaOuro,
    ProtocoloCamadaPrata,
    ProtocoloExecutorCiclo,
    ProtocoloExtratorComentarios,
    ProtocoloLematizador,
    ProtocoloRastreadorExperimentos,
    ProtocoloRotuladorTopicos,
)
from app.representacao_texto.fabrica_representacao import FabricaRepresentacao
from app.tratamento_texto.lematizador_spacy import LematizadorSpacy
from app.tratamento_texto.limpador_texto import LimpadorTexto
from app.tratamento_texto.rotulador_topicos import RotuladorTopicos

__all__ = ["ExecutorCiclo", "ProtocoloExecutorCiclo"]


class ExecutorCiclo:
    """Executa o pipeline completo sem gravação em disco local e com controle de exceções."""

    def __init__(
        self,
        config: ConfiguracaoGlobal,
        extrator: ProtocoloExtratorComentarios | ExtratorComentarios,
        bronze: ProtocoloCamadaBronze | CamadaBronze,
        prata: ProtocoloCamadaPrata | CamadaPrata,
        ouro: ProtocoloCamadaOuro | CamadaOuro,
        lematizador: ProtocoloLematizador | LematizadorSpacy,
        rotulador: ProtocoloRotuladorTopicos | RotuladorTopicos,
        calculador_tendencias: ProtocoloCalculadorTendencias | CalculadorTendencias,
        agregador_visoes: ProtocoloAgregadorVisoes | AgregadorVisoes,
        rastreador_mlflow: ProtocoloRastreadorExperimentos | RastreadorExperimentos | None = None,
    ) -> None:
        self._config: ConfiguracaoGlobal = config
        self._extrator: ProtocoloExtratorComentarios | ExtratorComentarios = extrator
        self._bronze: ProtocoloCamadaBronze | CamadaBronze = bronze
        self._prata: ProtocoloCamadaPrata | CamadaPrata = prata
        self._ouro: ProtocoloCamadaOuro | CamadaOuro = ouro
        self._lematizador: ProtocoloLematizador | LematizadorSpacy = lematizador
        self._rotulador: ProtocoloRotuladorTopicos | RotuladorTopicos = rotulador
        self._calculador: ProtocoloCalculadorTendencias | CalculadorTendencias = calculador_tendencias
        self._agregador: ProtocoloAgregadorVisoes | AgregadorVisoes = agregador_visoes
        self._rastreador: ProtocoloRastreadorExperimentos | RastreadorExperimentos | None = rastreador_mlflow

    def executar_ciclo_canal(self, id_canal: str) -> dict[str, int]:
        """Executa a sequência completa de coleta, processamento, ML e lakehouse para um canal."""
        inicio_ciclo = time.perf_counter()
        DespachanteAlertas.alertar_inicio_etapa(f"coleta_canal_{id_canal}")
        inicio_coleta = time.perf_counter()

        videos, comentarios = self._extrator.extrair_canal_completo(
            id_canal=id_canal,
            dias_retroativos=self._config.coleta.dias_publicacao_atras,
            incluir_respostas=self._config.coleta.incluir_respostas,
            limite_videos=self._config.coleta.limite_videos_por_canal,
            tamanho_pagina=self._config.coleta.tamanho_pagina,
        )
        duracao_coleta = time.perf_counter() - inicio_coleta
        HISTOGRAMA_ETAPAS_PIPELINE.labels(etapa="coleta").observe(duracao_coleta)
        MedidorColeta.registrar_comentarios_coletados(len(comentarios))
        DespachanteAlertas.alertar_sucesso_etapa(
            f"coleta_canal_{id_canal}", f"{len(videos)} vídeos, {len(comentarios)} comentários"
        )

        if not comentarios:
            duracao_total = time.perf_counter() - inicio_ciclo
            MedidorColeta.registrar_execucao_pipeline(
                duracao_segundos=round(duracao_total, 2),
                canal=id_canal,
                sucesso=True,
            )
            return {"videos": len(videos), "comentarios": 0, "topicos_ouro": 0}

        # 1. Persistência Bronze e Prata por vídeo, e catálogo na Ouro
        nome_canal = id_canal
        try:
            nome_canal, _ = self._extrator.obter_detalhes_canal(id_canal)
        except Exception:
            pass
        if videos:
            try:
                self._ouro.gravar_catalogo_videos(
                    id_canal=id_canal,
                    nome_canal=nome_canal,
                    videos=[(v.id_video, v.titulo) for v in videos],
                )
            except Exception:
                pass

        for video in videos:
            comms_video = [c for c in comentarios if c.id_video == video.id_video]
            if comms_video:
                self._bronze.gravar_lote_comentarios(id_canal, video.id_video, comms_video)
                self._prata.gravar_snapshot_comentarios(id_canal, video.id_video, comms_video)

        # 2. NLP: Normalização, lematização e representação vetorial
        textos_limpos = [LimpadorTexto.normalizar(c.texto_original) for c in comentarios]
        lemas_documentos = [self._lematizador.processar_texto(t) for t in textos_limpos]
        textos_para_vetorizar = [" ".join(lem) for lem in lemas_documentos]

        vetorizador = FabricaRepresentacao.criar_vetorizador(self._config.processamento)
        matriz_tfidf = vetorizador.ajustar_e_transformar(textos_para_vetorizar)

        # Seleciona o espaço vetorial para agrupamento: BERTimbau, embeddings densos (híbrido) ou TF-IDF
        if self._config.processamento.representacao.tecnica in ("bertimbau", "sentence_transformers"):
            extrator_bert = FabricaRepresentacao.criar_extrator_bertimbau(self._config.processamento)
            matriz_agrupamento = extrator_bert.extrair_vetores(textos_limpos)
        elif self._config.processamento.representacao.tecnica == "hibrida":
            extrator_emb = FabricaRepresentacao.criar_extrator_embeddings(self._config.processamento)
            matriz_agrupamento = extrator_emb.extrair_vetores(textos_limpos)
        else:
            matriz_agrupamento = matriz_tfidf

        # Aplicação opcional de redução de dimensionalidade (ex: UMAP ou SVD)
        redutor = FabricaRepresentacao.criar_redutor_opcional(self._config.processamento)
        if redutor is not None and len(comentarios) >= 4:
            matriz_agrupamento = redutor.ajustar_e_reduzir(matriz_agrupamento)

        # 3. Modelos de Clusterização
        tecnicas_ativas: list[str] = []
        if self._config.processamento.tecnicas.kmeans_ativo:
            tecnicas_ativas.append("kmeans")
        if self._config.processamento.tecnicas.dbscan_ativo:
            tecnicas_ativas.append("dbscan")
        if self._config.processamento.tecnicas.hdbscan_ativo:
            tecnicas_ativas.append("hdbscan")

        total_topicos_ouro = 0

        for tecnica in tecnicas_ativas:
            agrupador = FabricaAgrupadores.criar_agrupador(tecnica, self._config.processamento)
            rotulos, metricas = agrupador.ajustar_e_agrupar(matriz_agrupamento)


            MedidorModelos.atualizar_metricas_cluster(
                tecnica=tecnica,
                quantidade_clusters=metricas.quantidade_clusters,
                fracao_ruido=metricas.fracao_ruido,
                silhueta=metricas.pontuacao_silhueta,
            )

            # Extração de Tópicos (1 lema por cluster)
            topico_por_cluster: dict[int, str] = {}
            clusters_unicos = set(rotulos)

            for cid in clusters_unicos:
                if cid == -1:
                    topico_por_cluster[cid] = "sem_topico"
                    continue
                lemas_do_cluster = [
                    lemas_documentos[i] for i, r in enumerate(rotulos) if r == cid
                ]
                topico_eleito = self._rotulador.rotular_cluster(
                    lemas_do_cluster, lemas_documentos
                )
                topico_por_cluster[cid] = topico_eleito

            topicos_por_comentario: dict[str, str] = {}
            for i, com in enumerate(comentarios):
                rotulo_i = rotulos[i] if i < len(rotulos) else -1
                topicos_por_comentario[com.id_comentario] = topico_por_cluster.get(
                    rotulo_i, "sem_topico"
                )

            # 4. Tendências e Camada Ouro
            topicos_canal_acumulados: list[RegistroTopicoOuro] = []

            for video in videos:
                comms_video = [c for c in comentarios if c.id_video == video.id_video]
                if not comms_video:
                    continue

                regs_video = self._calculador.calcular_tendencias_video(
                    id_canal=id_canal,
                    id_video=video.id_video,
                    tecnica=tecnica,
                    topicos_por_comentario=topicos_por_comentario,
                    comentarios=comms_video,
                )
                if regs_video:
                    self._ouro.gravar_topicos_video(
                        id_canal=id_canal,
                        id_video=video.id_video,
                        tecnica=tecnica,
                        topicos=regs_video,
                    )
                    topicos_canal_acumulados.extend(regs_video)
                    total_topicos_ouro += len(regs_video)

            # Ouro Consolidado por Canal
            if topicos_canal_acumulados:
                regs_canal = self._agregador.consolidar_canal(
                    id_canal=id_canal,
                    tecnica=tecnica,
                    topicos_dos_videos=topicos_canal_acumulados,
                )
                self._ouro.gravar_topicos_canal_consolidado(
                    id_canal=id_canal,
                    tecnica=tecnica,
                    topicos=regs_canal,
                )

            # Rastreamento MLflow
            if self._rastreador is not None:
                try:
                    params_mlflow: dict[str, object] = {
                        "canal": id_canal,
                        "videos": len(videos),
                    }
                    fn_modelo = getattr(agrupador, "obter_modelo", None)
                    modelo_sklearn = fn_modelo() if callable(fn_modelo) else None
                    fn_k = getattr(agrupador, "obter_k_otimo", None)
                    if callable(fn_k):
                        params_mlflow["k_otimo"] = fn_k()

                    self._rastreador.registrar_execucao(
                        nome_experimento=self._config.projeto.nome,
                        tecnica=tecnica,
                        parametros=params_mlflow,
                        metricas=metricas,
                        uri_manifesto_s3=f"s3://{self._config.persistencia.bucket}/ouro/id_canal={id_canal}/",
                        modelo_sklearn=modelo_sklearn,
                        nome_modelo_registry=f"modelo_{tecnica}_youtube" if modelo_sklearn is not None else None,
                    )
                except Exception:
                    pass

        duracao_total = time.perf_counter() - inicio_ciclo
        MedidorColeta.registrar_execucao_pipeline(
            duracao_segundos=round(duracao_total, 2),
            canal=id_canal,
            sucesso=True,
        )

        return {
            "videos": len(videos),
            "comentarios": len(comentarios),
            "topicos_ouro": total_topicos_ouro,
        }
