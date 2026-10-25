"""Fábrica e roteamento da aplicação FastAPI para serviço analítico e predição."""

from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.analise_clusters.analisador_clusters import ROTULO_RUIDO
from app.conf_yaml import ConfigAPIInfo, ConfigClusteringInfo
from app.excecoes import ErroConfiguracao
from app.servico_api.esquemas import (
    RequisicaoLote,
    RequisicaoPonto,
    RespostaInfoModelo,
    RespostaPerfilCluster,
    RespostaPrevisaoLote,
    RespostaPrevisaoPonto,
    RespostaProntidao,
    RespostaResumoClusters,
    RespostaSaude,
)
from app.servico_api.estado_aplicacao import EstadoAplicacao

REQUISICOES_TOTAL = Counter(
    "clustering_api_requisicoes_total",
    "Total de requisições recebidas pela API de clustering",
    ["endpoint", "metodo", "status"],
)
LATENCIA_INFERENCIA = Histogram(
    "clustering_api_latencia_segundos",
    "Latência de processamento das requisições",
    ["endpoint"],
)


def _obter_estado_padrao() -> EstadoAplicacao:
    """Carrega o estado a partir do diretório config padrão se disponível."""
    diretorio_config = Path("config")
    if diretorio_config.exists():
        try:
            from app.conf_yaml import ConfYAML
            from app.gestao_datalake.repositorio_s3_lakehouse import (
                RepositorioS3Lakehouse,
            )

            conf = ConfYAML.carregar_de_diretorio(diretorio_config)
            repositorio = RepositorioS3Lakehouse(config=conf.datalake.datalake)
            return EstadoAplicacao(
                config_api=conf.api.api,
                config_clustering=conf.clustering.clustering,
                repositorio=repositorio,
                nomes_atributos=conf.atributos.atributos.treino.colunas,
            )
        except (ErroConfiguracao, OSError, ValueError, KeyError):
            return EstadoAplicacao()
    return EstadoAplicacao()


def criar_aplicacao_fastapi(estado: EstadoAplicacao | None = None) -> FastAPI:
    """Cria e configura a instância do FastAPI com base no estado e nas rotas autorizadas."""
    estado_ativo = estado if estado is not None else _obter_estado_padrao()
    config_api: ConfigAPIInfo = estado_ativo.config_api
    config_clustering: ConfigClusteringInfo = estado_ativo.config_clustering

    app = FastAPI(
        title="Plataforma de Clustering de Avaliações",
        description="API REST modular para inferência, consulta de clusters e métricas analíticas.",
        version="1.0.0",
    )

    # --------------------------------------------------------------------------
    # Rotas de Saúde, Prontidão e Métricas Operacionais
    # --------------------------------------------------------------------------

    @app.get(config_api.endpoints.health, response_model=RespostaSaude, tags=["Operação"])
    def verificar_saude() -> RespostaSaude:
        """Verifica se o processo da API está ativo e respondendo."""
        REQUISICOES_TOTAL.labels(endpoint="/health", metodo="GET", status="200").inc()
        return RespostaSaude(
            status="ok",
            versao="1.0.0",
            servicos={
                "api": "online",
                "motor_clustering": "ativo" if estado_ativo.motor is not None else "inativo",
                "lakehouse": "conectado" if estado_ativo.repositorio is not None else "desconectado",
            },
        )

    @app.get(config_api.endpoints.ready, response_model=RespostaProntidao, tags=["Operação"])
    def verificar_prontidao(response: Response) -> RespostaProntidao:
        """Verifica se os serviços dependentes e o modelo estão prontos para receber tráfego."""
        datalake_ok = estado_ativo.repositorio is not None
        modelo_ok = estado_ativo.motor is not None
        pronto = datalake_ok and modelo_ok

        detalhes = "Serviço totalmente operacional."
        if not modelo_ok:
            detalhes = "Modelo de clustering ainda não carregado em memória."
        elif not datalake_ok:
            detalhes = "Repositório Lakehouse indisponível."

        if not pronto:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        status_code = "200" if pronto else "503"
        REQUISICOES_TOTAL.labels(endpoint="/ready", metodo="GET", status=status_code).inc()

        return RespostaProntidao(
            pronto=pronto,
            datalake_acessivel=datalake_ok,
            modelo_carregado=modelo_ok,
            algoritmo_ativo=config_clustering.algoritmo if modelo_ok else None,
            detalhes=detalhes,
        )

    @app.get(config_api.endpoints.metrics, tags=["Observabilidade"])
    def exportar_metricas() -> Response:
        """Exporta métricas de aplicação no formato padrão Prometheus."""
        REQUISICOES_TOTAL.labels(endpoint="/metrics", metodo="GET", status="200").inc()
        conteudo = generate_latest()
        return Response(content=conteudo, media_type=CONTENT_TYPE_LATEST)

    # --------------------------------------------------------------------------
    # Rotas Analíticas e de Metadados do Modelo
    # --------------------------------------------------------------------------

    prefixo = config_api.prefixo

    @app.get(f"{prefixo}{config_api.endpoints.model}", response_model=RespostaInfoModelo, tags=["Modelo"])
    def obter_informacoes_modelo() -> RespostaInfoModelo:
        """Exibe metadados, suporte a inferência e lista de atributos esperados pelo modelo."""
        motor = estado_ativo.motor
        qtd_clusters = (
            estado_ativo.resumo_clusters.quantidade_clusters_validos
            if estado_ativo.resumo_clusters is not None
            else 0
        )

        return RespostaInfoModelo(
            modelo_carregado=motor is not None,
            algoritmo=config_clustering.algoritmo,
            motor=config_clustering.motor,
            tem_centroides=motor.tem_centroides if motor is not None else False,
            suporta_previsao=motor.suporta_previsao if motor is not None else False,
            quantidade_clusters=qtd_clusters,
            nomes_atributos_esperados=estado_ativo.nomes_atributos,
        )

    @app.get(f"{prefixo}{config_api.endpoints.clusters}", response_model=RespostaResumoClusters, tags=["Clusters"])
    def obter_resumo_clusters() -> RespostaResumoClusters:
        """Retorna sumário estatístico e perfis de todos os clusters formados."""
        resumo = estado_ativo.resumo_clusters
        if resumo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhum agrupamento foi processado ou registrado no estado atual.",
            )

        perfis_resposta: list[RespostaPerfilCluster] = [
            RespostaPerfilCluster(
                id_cluster=p.id_cluster,
                nome_rotulo=p.nome_rotulo,
                quantidade_amostras=p.quantidade_amostras,
                proporcao_amostras=p.proporcao_amostras,
                medias_atributos=p.medias_atributos,
                medianas_atributos=p.medianas_atributos,
                distancia_media_centroide=p.distancia_media_centroide,
                rotulo_negocio=p.rotulo_negocio,
                alerta_negocio=p.alerta_negocio,
                prioridade_negocio=p.prioridade_negocio,
                metricas_personalizadas=p.metricas_personalizadas,
            )
            for p in resumo.perfis
        ]

        return RespostaResumoClusters(
            algoritmo=config_clustering.algoritmo,
            total_amostras=resumo.total_amostras,
            quantidade_clusters_validos=resumo.quantidade_clusters_validos,
            quantidade_ruido=resumo.quantidade_ruido,
            proporcao_ruido=resumo.proporcao_ruido,
            perfis=perfis_resposta,
        )

    @app.get(
        f"{prefixo}{config_api.endpoints.clusters}/{{cluster_id}}",
        response_model=RespostaPerfilCluster,
        tags=["Clusters"],
    )
    def obter_perfil_cluster_por_id(cluster_id: int) -> RespostaPerfilCluster:
        """Retorna as estatísticas descritivas de um cluster específico."""
        resumo = estado_ativo.resumo_clusters
        if resumo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhum agrupamento disponível.",
            )

        perfil = next((p for p in resumo.perfis if p.id_cluster == cluster_id), None)
        if perfil is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cluster com id '{cluster_id}' não encontrado.",
            )

        return RespostaPerfilCluster(
            id_cluster=perfil.id_cluster,
            nome_rotulo=perfil.nome_rotulo,
            quantidade_amostras=perfil.quantidade_amostras,
            proporcao_amostras=perfil.proporcao_amostras,
            medias_atributos=perfil.medias_atributos,
            medianas_atributos=perfil.medianas_atributos,
            distancia_media_centroide=perfil.distancia_media_centroide,
            rotulo_negocio=perfil.rotulo_negocio,
            alerta_negocio=perfil.alerta_negocio,
            prioridade_negocio=perfil.prioridade_negocio,
            metricas_personalizadas=perfil.metricas_personalizadas,
        )

    # --------------------------------------------------------------------------
    # Rotas de Inferência / Predição (com validação estrita de algoritmo)
    # --------------------------------------------------------------------------

    def _validar_capacidade_previsao() -> None:
        motor = estado_ativo.motor
        if motor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Nenhum modelo de agrupamento está carregado para inferência.",
            )

        if not motor.suporta_previsao:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"O algoritmo configurado ('{config_clustering.algoritmo}') não suporta "
                    "previsão para novos pontos out-of-sample (característica esperada de algoritmos como DBSCAN/HDBSCAN)."
                ),
            )

    @app.post(f"{prefixo}{config_api.endpoints.predict}", response_model=RespostaPrevisaoPonto, tags=["Inferência"])
    def prever_ponto(requisicao: RequisicaoPonto) -> RespostaPrevisaoPonto:
        """Atribui um cluster a um novo ponto de dados."""
        _validar_capacidade_previsao()
        motor = estado_ativo.motor
        assert motor is not None

        with LATENCIA_INFERENCIA.labels(endpoint="/predict").time():
            # Converte atributos garantindo a ordem esperada
            if estado_ativo.nomes_atributos:
                valores: list[float] = []
                for nome_attr in estado_ativo.nomes_atributos:
                    if nome_attr not in requisicao.atributos:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Atributo obrigatório ausente: '{nome_attr}'",
                        )
                    valores.append(float(requisicao.atributos[nome_attr]))
            else:
                valores = [float(v) for v in requisicao.atributos.values()]

            vetor = np.array([valores], dtype=np.float64)
            rotulos = motor.prever(vetor)
            rotulo = rotulos[0]

            distancia: float | None = None
            if motor.tem_centroides and rotulo != -1:
                centroides = motor.obter_centroides()
                if centroides is not None and 0 <= rotulo < len(centroides):
                    distancia = float(np.linalg.norm(vetor[0] - centroides[rotulo]))

            nome = ROTULO_RUIDO if rotulo == -1 else f"Cluster {rotulo}"

            REQUISICOES_TOTAL.labels(endpoint="/predict", metodo="POST", status="200").inc()

            return RespostaPrevisaoPonto(
                cluster_atribuido=rotulo,
                nome_rotulo=nome,
                algoritmo=config_clustering.algoritmo,
                distancia_centroide=distancia,
            )

    @app.post(
        f"{prefixo}{config_api.endpoints.predict_batch}",
        response_model=RespostaPrevisaoLote,
        tags=["Inferência"],
    )
    def prever_lote(requisicao: RequisicaoLote) -> RespostaPrevisaoLote:
        """Atribui clusters a um lote de amostras concorrentemente."""
        _validar_capacidade_previsao()
        motor = estado_ativo.motor
        assert motor is not None

        limite_maximo = config_api.limites.tamanho_lote_maximo
        total_amostras = len(requisicao.amostras)

        if total_amostras == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lote de amostras não pode ser vazio.",
            )

        if total_amostras > limite_maximo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tamanho do lote ({total_amostras}) excede o limite configurado de {limite_maximo}.",
            )

        with LATENCIA_INFERENCIA.labels(endpoint="/predict-batch").time():
            matriz_lista: list[list[float]] = []
            for idx, item in enumerate(requisicao.amostras):
                if estado_ativo.nomes_atributos:
                    linha: list[float] = []
                    for nome_attr in estado_ativo.nomes_atributos:
                        if nome_attr not in item:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Atributo '{nome_attr}' ausente na amostra de índice {idx}.",
                            )
                        linha.append(float(item[nome_attr]))
                    matriz_lista.append(linha)
                else:
                    matriz_lista.append([float(v) for v in item.values()])

            matriz = np.array(matriz_lista, dtype=np.float64)
            rotulos = motor.prever(matriz)

            REQUISICOES_TOTAL.labels(endpoint="/predict-batch", metodo="POST", status="200").inc()

            return RespostaPrevisaoLote(
                clusters_atribuidos=rotulos,
                total_amostras=total_amostras,
                algoritmo=config_clustering.algoritmo,
            )

    return app


criar_aplicacao = criar_aplicacao_fastapi
