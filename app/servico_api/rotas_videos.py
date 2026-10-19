from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Request

from app.configuracao_geral.tipos_enumerados import TecnicaCluster
from app.gestao_dados.camada_ouro import CamadaOuro
from app.servico_api.esquemas_respostas import (
    DetalheCentroide,
    RespostaCentroidesVideo,
    RespostaClustersVideo,
    RespostaComentariosTopico,
    RespostaEstatisticaCluster,
    RespostaTendenciasVideo,
    RespostaTopicoItem,
    TermoCentroide,
)

roteador_videos = APIRouter(prefix="/v1/canais/{id_canal}/videos", tags=["videos"])


@roteador_videos.get("/{id_video}/tendencias", response_model=RespostaTendenciasVideo)
def obter_tendencias_video(
    id_canal: str,
    id_video: str,
    request: Request,
    tecnica: TecnicaCluster = Query(TecnicaCluster.KMEANS, description="Técnica de agrupamento"),
    data: str | None = Query(None, description="Data da tendência no formato AAAA-MM-DD (ex: 2026-10-14). Se omitido, busca o dia mais recente."),
) -> RespostaTendenciasVideo:
    """Consulta os tópicos e tendências de um vídeo específico na camada Ouro."""
    camada_ouro: CamadaOuro | None = getattr(request.app.state, "camada_ouro", None)
    if camada_ouro is None:
        raise HTTPException(status_code=500, detail="Serviço de persistência não configurado na API.")

    registros = []
    try:
        chave = camada_ouro.obter_chave_tendencias(
            id_canal=id_canal,
            tecnica=str(tecnica),
            data=data,
            consolidado=False,
            id_video=id_video,
        )
        registros = camada_ouro.carregar_topicos(chave)
    except Exception:
        registros = []

    data_efetiva = (
        (registros[0].data_referencia if registros and registros[0].data_referencia else "")
        or data
        or datetime.now(timezone.utc).strftime("%Y-%m-%d")
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

    return RespostaTendenciasVideo(
        id_canal=id_canal,
        id_video=id_video,
        tecnica=tecnica,
        topicos=itens,
        data_referencia=data_efetiva,
    )


@roteador_videos.get("/{id_video}/clusters", response_model=RespostaClustersVideo)
def obter_clusters_video(
    id_canal: str,
    id_video: str,
    request: Request,
    tecnica: TecnicaCluster = Query(TecnicaCluster.KMEANS, description="Técnica de clusterização"),
    data: str | None = Query(None, description="Data analítica no formato AAAA-MM-DD. Se omitido, busca o dia mais recente."),
) -> RespostaClustersVideo:
    """Retorna o agrupamento estrutural e distribuição de clusters do vídeo."""
    camada_ouro: CamadaOuro | None = getattr(request.app.state, "camada_ouro", None)
    if camada_ouro is None:
        raise HTTPException(status_code=500, detail="Serviço de persistência não configurado.")

    try:
        chave = camada_ouro.obter_chave_tendencias(
            id_canal=id_canal,
            tecnica=str(tecnica),
            data=data,
            consolidado=False,
            id_video=id_video,
        )
        registros = camada_ouro.carregar_topicos(chave)
    except Exception:
        registros = []

    total_comentarios = sum(r.contagem_atual for r in registros) or 1
    clusters_resp: list[RespostaEstatisticaCluster] = []

    for idx, reg in enumerate(registros):
        perc = (reg.contagem_atual / total_comentarios) * 100.0
        clusters_resp.append(
            RespostaEstatisticaCluster(
                cluster_id=idx,
                rotulo_topico=reg.topico,
                total_comentarios=reg.contagem_atual,
                percentual_total=round(perc, 2),
            )
        )

    ruido_contagem = sum(r.contagem_atual for r in registros if r.topico == "sem_topico")
    fracao_ruido = round(ruido_contagem / total_comentarios, 4)

    return RespostaClustersVideo(
        id_canal=id_canal,
        id_video=id_video,
        tecnica=tecnica,
        quantidade_clusters=len(clusters_resp),
        fracao_ruido=fracao_ruido,
        clusters=clusters_resp,
    )


@roteador_videos.get(
    "/{id_video}/topicos/{topico}/comentarios",
    response_model=RespostaComentariosTopico,
)
def obter_comentarios_topico(
    id_canal: str,
    id_video: str,
    topico: str,
    request: Request,
    tecnica: TecnicaCluster = Query(TecnicaCluster.KMEANS, description="Técnica de clusterização"),
    data: str | None = Query(None, description="Data analítica no formato AAAA-MM-DD. Se omitido, busca o dia mais recente."),
    pagina: int = Query(1, ge=1, description="Número da página de comentários"),
    tamanho_pagina: int = Query(10, ge=1, le=100, description="Tamanho da página"),
) -> RespostaComentariosTopico:
    """Retorna comentários associados a um determinado tópico com suporte a paginação."""
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
                consolidado=False,
                id_video=id_video,
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
                consolidado=False,
                id_video=id_video,
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
                    consolidado=False,
                    id_video=id_video,
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
        id_video=id_video,
        topico=topico,
        tecnica=tecnica,
        pagina=pagina,
        total_amostras=len(comentarios_encontrados),
        comentarios=itens_pagina,
    )


@roteador_videos.get("/{id_video}/centroides", response_model=RespostaCentroidesVideo)
def obter_centroides_video(
    id_canal: str,
    id_video: str,
    request: Request,
    tecnica: TecnicaCluster = Query(TecnicaCluster.KMEANS, description="Técnica de clusterização"),
    data: str | None = Query(None, description="Data analítica no formato AAAA-MM-DD. Se omitido, busca o dia mais recente."),
    top_termos_limite: int = Query(5, ge=1, le=20, description="Quantidade de termos principais por centróide"),
) -> RespostaCentroidesVideo:
    """Extrai os centróides semânticos dos clusters do vídeo, incluindo termos dominantes e comentários protótipo."""
    camada_ouro: CamadaOuro | None = getattr(request.app.state, "camada_ouro", None)
    if camada_ouro is None:
        raise HTTPException(status_code=500, detail="Serviço de persistência não configurado.")

    try:
        chave = camada_ouro.obter_chave_tendencias(
            id_canal=id_canal,
            tecnica=str(tecnica),
            data=data,
            consolidado=False,
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

    return RespostaCentroidesVideo(
        id_canal=id_canal,
        id_video=id_video,
        tecnica=tecnica,
        total_clusters=len(detalhes_centroides),
        centroides=detalhes_centroides,
    )

