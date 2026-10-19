"""Rotas da API para consultas agregadas em nível de canal."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, Request

from app.coleta_youtube.cliente_youtube import ClienteYouTube
from app.configuracao_geral.tipos_enumerados import TecnicaCluster
from app.gestao_dados.camada_ouro import CamadaOuro
from app.servico_api.esquemas_respostas import (
    DetalheCentroide,
    ItemVideoCatalogo,
    RespostaCatalogoVideosCanal,
    RespostaCentroidesCanal,
    RespostaComentariosTopico,
    RespostaSerieTemporalTopico,
    RespostaTendenciasCanal,
    RespostaTopicoItem,
    TermoCentroide,
)


roteador_canais = APIRouter(prefix="/v1/canais", tags=["canais"])


@roteador_canais.get("/{id_canal}/videos", response_model=RespostaCatalogoVideosCanal)
@roteador_canais.get("/{id_canal}", response_model=RespostaCatalogoVideosCanal, include_in_schema=False)
def listar_videos_canal(
    id_canal: str,
    request: Request,
) -> RespostaCatalogoVideosCanal:
    """Retorna o nome do canal, id dos vídeos e títulos dos vídeos associados."""
    camada_ouro: CamadaOuro | None = getattr(request.app.state, "camada_ouro", None)
    cliente_youtube: ClienteYouTube | None = getattr(request.app.state, "cliente_youtube", None)

    nome_canal = id_canal
    lista_videos: list[tuple[str, str]] = []

    # 1. Tenta recuperar catálogo persistido no Lakehouse Ouro (Parquet no S3)
    if camada_ouro is not None:
        try:
            nome_canal, lista_videos = camada_ouro.carregar_catalogo_videos(id_canal)
        except Exception:
            lista_videos = []

    # 2. Se catálogo ainda não estiver gravado no S3 e cliente YouTube estiver disponível, consulta a API
    if not lista_videos and cliente_youtube is not None:
        try:
            nome_canal, _ = cliente_youtube.obter_detalhes_canal(id_canal)
            data_limite = datetime.now(timezone.utc) - timedelta(days=365)
            metadados = cliente_youtube.listar_videos_recentes(id_canal, data_limite, limite_videos=50)
            lista_videos = [(v.id_video, v.titulo) for v in metadados]

            # Grava no S3 para acelerar consultas subsequentes
            if camada_ouro is not None and lista_videos:
                try:
                    camada_ouro.gravar_catalogo_videos(id_canal, nome_canal, lista_videos)
                except Exception:
                    pass
        except Exception:
            pass

    # 3. Fallback: Se não conseguiu nomes mas há partições de vídeos processadas na Camada Ouro
    if not lista_videos and camada_ouro is not None:
        try:
            vids_conhecidos = camada_ouro.listar_videos_conhecidos(id_canal)
            if vids_conhecidos:
                lista_videos = [(vid, f"Vídeo {vid}") for vid in vids_conhecidos]
        except Exception:
            pass

    if not lista_videos and nome_canal == id_canal:
        raise HTTPException(
            status_code=404,
            detail=f"Canal '{id_canal}' não encontrado ou sem vídeos disponíveis.",
        )

    itens = [
        ItemVideoCatalogo(id_video=vid, nome_video=nome)
        for vid, nome in lista_videos
    ]

    return RespostaCatalogoVideosCanal(
        id_canal=id_canal,
        nome_canal=nome_canal,
        total_videos=len(itens),
        videos=itens,
    )


@roteador_canais.get("/{id_canal}/tendencias", response_model=RespostaTendenciasCanal)
def obter_tendencias_canal(
    id_canal: str,
    request: Request,
    tecnica: TecnicaCluster = Query(TecnicaCluster.KMEANS, description="Técnica de clusterização (kmeans, dbscan, hdbscan)"),
    data: str | None = Query(None, description="Data da tendência no formato AAAA-MM-DD (ex: 2026-10-14). Se omitido, busca o dia mais recente."),
) -> RespostaTendenciasCanal:
    """Retorna as tendências consolidadas de um canal a partir dos dados do lakehouse Ouro."""
    camada_ouro: CamadaOuro | None = getattr(request.app.state, "camada_ouro", None)
    if camada_ouro is None:
        raise HTTPException(status_code=500, detail="Serviço de persistência não configurado na API.")

    registros = []
    # 1. Tenta obter a chave dinâmica por data (ou mais recente)
    try:
        chave = camada_ouro.obter_chave_tendencias(
            id_canal=id_canal,
            tecnica=str(tecnica),
            data=data,
            consolidado=True,
        )
        registros = camada_ouro.carregar_topicos(chave)
    except Exception:
        registros = []

    data_efetiva = (
        (registros[0].data_referencia if registros and registros[0].data_referencia else "")
        or data
        or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )

    if not registros:
        return RespostaTendenciasCanal(
            id_canal=id_canal,
            tecnica=tecnica,
            topicos=[],
            data_referencia=data_efetiva,
        )

    itens = [
        RespostaTopicoItem(
            topico=r.topico,
            contagem_atual=r.contagem_atual,
            contagem_anterior=r.contagem_anterior,
            variacao_proporcao=r.variacao_proporcao,
            status_tendencia=r.status_tendencia,
            comentarios=[
                a.strip()
                for a in (
                    r.comentarios_amostra.split("|||")
                    if "|||" in r.comentarios_amostra
                    else r.comentarios_amostra.split(",")
                )
                if a.strip()
            ],
            percentual_variacao=r.percentual_variacao,
            data_referencia=r.data_referencia or data_efetiva,
        )
        for r in registros
    ]

    return RespostaTendenciasCanal(
        id_canal=id_canal,
        tecnica=tecnica,
        topicos=itens,
        data_referencia=data_efetiva,
    )


@roteador_canais.get("/{id_canal}/centroides", response_model=RespostaCentroidesCanal)
def obter_centroides_canal(
    id_canal: str,
    request: Request,
    id_video: str | None = Query(None, description="Identificador opcional de vídeo para filtrar centróides"),
    tecnica: TecnicaCluster = Query(TecnicaCluster.KMEANS, description="Técnica de clusterização"),
    data: str | None = Query(None, description="Data analítica no formato AAAA-MM-DD. Se omitido, busca o dia mais recente."),
    top_termos_limite: int = Query(5, ge=1, le=20, description="Quantidade de termos principais por centróide"),
) -> RespostaCentroidesCanal:
    """Retorna os centróides semânticos dos clusters do canal ou filtrado por vídeo específico."""
    camada_ouro: CamadaOuro | None = getattr(request.app.state, "camada_ouro", None)
    if camada_ouro is None:
        raise HTTPException(status_code=500, detail="Serviço de persistência não configurado na API.")

    try:
        chave = camada_ouro.obter_chave_tendencias(
            id_canal=id_canal,
            tecnica=str(tecnica),
            data=data,
            consolidado=(not bool(id_video)),
            id_video=id_video,
        )
        registros = camada_ouro.carregar_topicos(chave)
    except Exception:
        registros = []

    detalhes_centroides: list[DetalheCentroide] = []

    cfg = getattr(request.app.state, "configuracao_global", None)
    stopwords_filtro: set[str] = {"que", "com", "para", "uma", "este", "esse", "isso", "por", "mais"}
    if cfg is not None and hasattr(cfg, "processamento") and getattr(cfg.processamento.stopwords, "filtro_centroides", None):
        stopwords_filtro = set(cfg.processamento.stopwords.filtro_centroides)

    for idx, reg in enumerate(registros):
        amostras = [
            a.strip()
            for a in (
                reg.comentarios_amostra.split("|||")
                if "|||" in reg.comentarios_amostra
                else reg.comentarios_amostra.split(",")
            )
            if a.strip()
        ]
        comentario_prototipo = amostras[0] if amostras else None

        termos_unicos: dict[str, float] = {}
        if reg.topico and reg.topico != "sem_topico":
            termos_unicos[reg.topico] = 1.0

        for amostra in amostras:
            palavras = [
                p.strip().lower()
                for p in amostra.replace(".", " ").replace(",", " ").replace("!", " ").replace("?", " ").split()
                if len(p.strip()) >= 3 and p.strip().lower() not in stopwords_filtro
            ]
            for palavra in palavras:
                if palavra not in termos_unicos:
                    termos_unicos[palavra] = round(0.8 / (1.0 + len(termos_unicos)), 4)
                if len(termos_unicos) >= top_termos_limite:
                    break
            if len(termos_unicos) >= top_termos_limite:
                break

        top_termos = [
            TermoCentroide(termo=t, peso=p)
            for t, p in sorted(termos_unicos.items(), key=lambda item: item[1], reverse=True)[:top_termos_limite]
        ]

        detalhes_centroides.append(
            DetalheCentroide(
                cluster_id=idx,
                rotulo_topico=reg.topico,
                total_comentarios=reg.contagem_atual,
                top_termos=top_termos,
                comentario_exemplar=comentario_prototipo,
            )
        )

    return RespostaCentroidesCanal(
        id_canal=id_canal,
        id_video=id_video,
        tecnica=tecnica,
        total_clusters=len(detalhes_centroides),
        centroides=detalhes_centroides,
    )


@roteador_canais.get("/{id_canal}/topicos/{topico}/serie_temporal", response_model=RespostaSerieTemporalTopico)
def obter_serie_temporal_topico(
    id_canal: str,
    topico: str,
    request: Request,
    tecnica: TecnicaCluster = Query(TecnicaCluster.KMEANS, description="Técnica de clusterização"),
) -> RespostaSerieTemporalTopico:
    """Retorna a série temporal da contagem e variação diária de um tópico específico ao longo dos dias."""
    from app.servico_api.esquemas_respostas import RespostaPontoSerieTemporal

    camada_ouro: CamadaOuro | None = getattr(request.app.state, "camada_ouro", None)
    if camada_ouro is None:
        raise HTTPException(status_code=500, detail="Serviço de persistência não configurado na API.")

    datas_disponiveis = camada_ouro.listar_datas_tendencias(
        id_canal=id_canal,
        tecnica=str(tecnica),
        consolidado=True,
    )

    pontos: list[RespostaPontoSerieTemporal] = []
    topico_alvo = topico.strip().lower()

    for d in sorted(datas_disponiveis):
        try:
            chave = camada_ouro.obter_chave_tendencias(
                id_canal=id_canal,
                tecnica=str(tecnica),
                data=d,
                consolidado=True,
            )
            regs = camada_ouro.carregar_topicos(chave)
            topico_encontrado = next((r for r in regs if r.topico.lower() == topico_alvo), None)
            if topico_encontrado is not None:
                pontos.append(
                    RespostaPontoSerieTemporal(
                        data=d,
                        contagem=topico_encontrado.contagem_atual,
                        percentual_variacao=topico_encontrado.percentual_variacao,
                        status_tendencia=topico_encontrado.status_tendencia,
                    )
                )
            else:
                pontos.append(
                    RespostaPontoSerieTemporal(
                        data=d,
                        contagem=0,
                        percentual_variacao=0.0,
                        status_tendencia="sem_dados",
                    )
                )
        except Exception:
            continue

    return RespostaSerieTemporalTopico(
        id_canal=id_canal,
        topico=topico,
        tecnica=tecnica,
        pontos=pontos,
    )


@roteador_canais.get(
    "/{id_canal}/topicos/{topico}/comentarios",
    response_model=RespostaComentariosTopico,
)
def obter_comentarios_topico_canal(
    id_canal: str,
    topico: str,
    request: Request,
    tecnica: TecnicaCluster = Query(TecnicaCluster.KMEANS, description="Técnica de clusterização"),
    data: str | None = Query(None, description="Data analítica no formato AAAA-MM-DD. Se omitido, agrega todos os comentários históricos acumulados."),
    pagina: int = Query(1, ge=1, description="Número da página de comentários"),
    tamanho_pagina: int = Query(10, ge=1, le=100, description="Tamanho da página"),
) -> RespostaComentariosTopico:
    """Retorna todos os comentários associados a um determinado tópico em nível consolidado de canal."""
    camada_ouro: CamadaOuro | None = getattr(request.app.state, "camada_ouro", None)
    if camada_ouro is None:
        raise HTTPException(status_code=500, detail="Serviço de persistência não configurado.")

    topico_alvo = topico.strip().lower()
    comentarios_encontrados: list[str] = []
    vistos: set[str] = set()

    datas_busca: list[str] = []
    if data:
        datas_busca = [data]
    else:
        try:
            res_datas = camada_ouro.listar_datas_tendencias(
                id_canal=id_canal,
                tecnica=str(tecnica),
                consolidado=True,
            )
            datas_busca = list(res_datas)
        except Exception:
            datas_busca = []

    if not datas_busca:
        try:
            chave_padrao = camada_ouro.obter_chave_tendencias(
                id_canal=id_canal,
                tecnica=str(tecnica),
                data=data,
                consolidado=True,
            )
            registros = camada_ouro.carregar_topicos(chave_padrao)
            for reg in registros:
                if reg.topico.lower() == topico_alvo:
                    amostras = (
                        reg.comentarios_amostra.split("|||")
                        if "|||" in reg.comentarios_amostra
                        else reg.comentarios_amostra.split(",")
                    )
                    for a in amostras:
                        limpo = a.strip()
                        if limpo and limpo not in vistos:
                            vistos.add(limpo)
                            comentarios_encontrados.append(limpo)
        except Exception:
            pass
    else:
        for d in datas_busca:
            try:
                chave = camada_ouro.obter_chave_tendencias(
                    id_canal=id_canal,
                    tecnica=str(tecnica),
                    data=d,
                    consolidado=True,
                )
                registros = camada_ouro.carregar_topicos(chave)
                for reg in registros:
                    if reg.topico.lower() == topico_alvo:
                        amostras = (
                            reg.comentarios_amostra.split("|||")
                            if "|||" in reg.comentarios_amostra
                            else reg.comentarios_amostra.split(",")
                        )
                        for a in amostras:
                            limpo = a.strip()
                            if limpo and limpo not in vistos:
                                vistos.add(limpo)
                                comentarios_encontrados.append(limpo)
            except Exception:
                continue

    inicio = (pagina - 1) * tamanho_pagina
    fim = inicio + tamanho_pagina
    itens_pagina = comentarios_encontrados[inicio:fim]

    return RespostaComentariosTopico(
        id_canal=id_canal,
        id_video=None,
        topico=topico,
        tecnica=tecnica,
        pagina=pagina,
        total_amostras=len(comentarios_encontrados),
        comentarios=itens_pagina,
    )




