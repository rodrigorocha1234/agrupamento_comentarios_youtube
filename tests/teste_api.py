"""Testes funcionais completos dos endpoints da API FastAPI."""

from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.gestao_dados.camada_ouro import CamadaOuro, RegistroTopicoOuro
from app.integracao_mlflow.adaptador_serving import AdaptadorServing
from app.servico_api.aplicacao_fastapi import criar_aplicacao


def test_endpoint_health() -> None:
    """Verifica disponibilidade do endpoint de saúde do sistema."""
    app = criar_aplicacao()
    cliente = TestClient(app)
    resp = cliente.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "saudavel"


def test_endpoints_tendencias_e_clusters() -> None:
    """Testa consultas analíticas à camada Ouro para canal, vídeo e clusters."""
    camada_ouro_mock = MagicMock(spec=CamadaOuro)
    reg_topico = RegistroTopicoOuro(
        id_canal="UC_EXEMPLO",
        id_video="VID_1",
        tecnica="kmeans",
        topico="python",
        contagem_atual=20,
        contagem_anterior=10,
        variacao_proporcao=1.0,
        status_tendencia="crescendo",
        comentarios_amostra="C1,C2,C3",
        janela="7dias",
    )
    camada_ouro_mock.carregar_topicos.return_value = [reg_topico]

    app = criar_aplicacao(camada_ouro=camada_ouro_mock)
    cliente = TestClient(app)

    # 1. Tendências do Canal
    resp_canal = cliente.get("/v1/canais/UC_EXEMPLO/tendencias?tecnica=kmeans")
    assert resp_canal.status_code == 200
    dados_canal = resp_canal.json()
    assert dados_canal["id_canal"] == "UC_EXEMPLO"
    assert len(dados_canal["topicos"]) == 1
    assert dados_canal["topicos"][0]["topico"] == "python"
    assert dados_canal["topicos"][0]["comentarios"] == ["C1", "C2", "C3"]

    # 2. Tendências do Vídeo
    resp_video = cliente.get("/v1/canais/UC_EXEMPLO/videos/VID_1/tendencias?tecnica=kmeans")
    assert resp_video.status_code == 200
    dados_video = resp_video.json()
    assert dados_video["id_video"] == "VID_1"
    assert dados_video["topicos"][0]["status_tendencia"] == "crescendo"
    assert dados_video["topicos"][0]["comentarios"] == ["C1", "C2", "C3"]

    # 3. Estatísticas de Clusters do Vídeo
    resp_clusters = cliente.get("/v1/canais/UC_EXEMPLO/videos/VID_1/clusters?tecnica=kmeans")
    assert resp_clusters.status_code == 200
    dados_clusters = resp_clusters.json()
    assert dados_clusters["quantidade_clusters"] == 1
    assert dados_clusters["clusters"][0]["rotulo_topico"] == "python"

    # 4. Detalhes Semânticos dos Centróides
    resp_centroides = cliente.get("/v1/canais/UC_EXEMPLO/videos/VID_1/centroides?tecnica=kmeans&top_termos_limite=3")
    assert resp_centroides.status_code == 200
    dados_centroides = resp_centroides.json()
    assert dados_centroides["id_canal"] == "UC_EXEMPLO"
    assert dados_centroides["id_video"] == "VID_1"
    assert dados_centroides["total_clusters"] == 1
    assert len(dados_centroides["centroides"]) == 1
    c0 = dados_centroides["centroides"][0]
    assert c0["rotulo_topico"] == "python"
    assert len(c0["top_termos"]) >= 1
    assert c0["top_termos"][0]["termo"] == "python"
    assert c0["comentario_exemplar"] == "C1"

    # 4. Comentários do Tópico Paginados (Vídeo)
    resp_comms = cliente.get(
        "/v1/canais/UC_EXEMPLO/videos/VID_1/topicos/python/comentarios?pagina=1&tamanho_pagina=2"
    )
    assert resp_comms.status_code == 200
    dados_comms = resp_comms.json()
    assert dados_comms["topico"] == "python"
    assert dados_comms["total_amostras"] == 3
    assert len(dados_comms["comentarios"]) == 2

    # 5. Comentários do Tópico Paginados (Canal Consolidado)
    resp_comms_canal = cliente.get(
        "/v1/canais/UC_EXEMPLO/topicos/python/comentarios?pagina=1&tamanho_pagina=2"
    )
    assert resp_comms_canal.status_code == 200
    dados_comms_canal = resp_comms_canal.json()
    assert dados_comms_canal["id_canal"] == "UC_EXEMPLO"
    assert dados_comms_canal["id_video"] is None
    assert dados_comms_canal["topico"] == "python"
    assert dados_comms_canal["total_amostras"] == 3
    assert len(dados_comms_canal["comentarios"]) == 2


def test_endpoint_inferencias_integrado_serving() -> None:
    """Testa envio de predições para o endpoint /v1/inferencias."""
    adaptador_mock = MagicMock(spec=AdaptadorServing)
    adaptador_mock.invocar_predicao.return_value = [0, 1]

    app = criar_aplicacao(adaptador_serving=adaptador_mock)
    cliente = TestClient(app)

    payload = {"textos": ["Comentário um", "Comentário dois"]}
    resp = cliente.post("/v1/inferencias", json=payload)

    assert resp.status_code == 200
    dados = resp.json()
    assert dados["predicoes"] == [0, 1]
    assert dados["total_amostras"] == 2
    adaptador_mock.invocar_predicao.assert_called_once_with(["Comentário um", "Comentário dois"])


def test_endpoint_listar_videos_canal() -> None:
    """Testa consulta ao endpoint /v1/canais/{id_canal}/videos com Lakehouse Ouro e fallback."""
    from datetime import datetime, timezone
    from app.coleta_youtube.cliente_youtube import ClienteYouTube
    from app.coleta_youtube.modelos_coleta import MetadadosVideo

    camada_ouro_mock = MagicMock(spec=CamadaOuro)
    camada_ouro_mock.carregar_catalogo_videos.return_value = (
        "Canal de Teste",
        [("VID_101", "Vídeo de Engenharia"), ("VID_102", "Vídeo de MLOps")],
    )

    app = criar_aplicacao(camada_ouro=camada_ouro_mock)
    cliente = TestClient(app)

    # 1. Consulta com dados presentes na camada Ouro
    resp = cliente.get("/v1/canais/UC_EXEMPLO/videos")
    assert resp.status_code == 200
    dados = resp.json()
    assert dados["id_canal"] == "UC_EXEMPLO"
    assert dados["nome_canal"] == "Canal de Teste"
    assert dados["total_videos"] == 2
    assert dados["videos"][0]["id_video"] == "VID_101"
    assert dados["videos"][0]["nome_video"] == "Vídeo de Engenharia"

    # 2. Teste via Cliente YouTube quando S3 não tem o catálogo
    camada_ouro_vazia = MagicMock(spec=CamadaOuro)
    camada_ouro_vazia.carregar_catalogo_videos.side_effect = Exception("Não encontrado")
    camada_ouro_vazia.listar_videos_conhecidos.return_value = []

    cliente_yt_mock = MagicMock(spec=ClienteYouTube)
    cliente_yt_mock.obter_detalhes_canal.return_value = ("Canal YouTube API", "PL_UPLOADS")
    cliente_yt_mock.listar_videos_recentes.return_value = [
        MetadadosVideo(
            id_video="VID_YT_1",
            id_canal="UC_YT",
            titulo="Vídeo Fresco do YouTube",
            publicado_em=datetime.now(timezone.utc),
        )
    ]

    app_yt = criar_aplicacao(camada_ouro=camada_ouro_vazia, cliente_youtube=cliente_yt_mock)
    cliente_test_yt = TestClient(app_yt)
    resp_yt = cliente_test_yt.get("/v1/canais/UC_YT/videos")
    assert resp_yt.status_code == 200
    dados_yt = resp_yt.json()
    assert dados_yt["nome_canal"] == "Canal YouTube API"
    assert len(dados_yt["videos"]) == 1
    assert dados_yt["videos"][0]["id_video"] == "VID_YT_1"
    assert dados_yt["videos"][0]["nome_video"] == "Vídeo Fresco do YouTube"


def test_endpoint_centroides_canal_e_video() -> None:
    """Verifica a busca de centróides em nível de canal (consolidado) e filtrado por vídeo."""
    camada_ouro_mock = MagicMock(spec=CamadaOuro)
    reg_topico = RegistroTopicoOuro(
        id_canal="UC_CANAL_CENTROIDE",
        id_video="VID_CENTROIDE",
        tecnica="kmeans",
        topico="ia",
        contagem_atual=15,
        contagem_anterior=5,
        variacao_proporcao=2.0,
        status_tendencia="crescendo",
        comentarios_amostra="IA aplicada no YouTube|||Inteligência artificial excelente",
        data_referencia="2026-10-14",
    )
    camada_ouro_mock.carregar_topicos.return_value = [reg_topico]
    def mock_obter_chave_centroides(
        id_canal: str,
        tecnica: str,
        data: str | None = None,
        consolidado: bool = True,
        id_video: str | None = None,
        **kw: object,
    ) -> str:
        if consolidado or not id_video:
            return f"ouro/id_canal={id_canal}/consolidado/tecnica={tecnica}/data={data or '2026-10-14'}/topicos.parquet"
        return f"ouro/id_canal={id_canal}/id_video={id_video}/tecnica={tecnica}/data={data or '2026-10-14'}/topicos.parquet"

    camada_ouro_mock.obter_chave_tendencias.side_effect = mock_obter_chave_centroides

    app = criar_aplicacao(camada_ouro=camada_ouro_mock)
    cliente = TestClient(app)

    # 1. Consulta em nível de canal (sem id_video) -> busca chave consolidada
    resp_canal = cliente.get("/v1/canais/UC_CANAL_CENTROIDE/centroides?tecnica=kmeans&top_termos_limite=4&data=2026-10-14")
    assert resp_canal.status_code == 200
    dados_canal = resp_canal.json()
    assert dados_canal["id_canal"] == "UC_CANAL_CENTROIDE"
    assert dados_canal["id_video"] is None
    assert dados_canal["total_clusters"] == 1
    assert dados_canal["centroides"][0]["rotulo_topico"] == "ia"
    assert dados_canal["centroides"][0]["comentario_exemplar"] == "IA aplicada no YouTube"
    camada_ouro_mock.carregar_topicos.assert_called_with(
        "ouro/id_canal=UC_CANAL_CENTROIDE/consolidado/tecnica=kmeans/data=2026-10-14/topicos.parquet"
    )

    # 2. Consulta filtrada por vídeo -> busca chave do vídeo
    resp_video = cliente.get("/v1/canais/UC_CANAL_CENTROIDE/centroides?id_video=VID_CENTROIDE&tecnica=kmeans&data=2026-10-14")
    assert resp_video.status_code == 200
    dados_video = resp_video.json()
    assert dados_video["id_canal"] == "UC_CANAL_CENTROIDE"
    assert dados_video["id_video"] == "VID_CENTROIDE"
    assert dados_video["total_clusters"] == 1
    assert dados_video["centroides"][0]["rotulo_topico"] == "ia"
    camada_ouro_mock.carregar_topicos.assert_called_with(
        "ouro/id_canal=UC_CANAL_CENTROIDE/id_video=VID_CENTROIDE/tecnica=kmeans/data=2026-10-14/topicos.parquet"
    )


def test_endpoint_serie_temporal_topico() -> None:
    """Verifica a recuperação da série temporal histórica de um tópico específico ao longo dos dias."""
    camada_ouro_mock = MagicMock(spec=CamadaOuro)
    camada_ouro_mock.listar_datas_tendencias.return_value = ["2026-10-14", "2026-10-15"]

    reg_dia1 = RegistroTopicoOuro(
        id_canal="UC_TIME",
        id_video="consolidado",
        tecnica="kmeans",
        topico="python",
        contagem_atual=10,
        contagem_anterior=0,
        variacao_proporcao=1.0,
        status_tendencia="novo",
        comentarios_amostra="Python dia 1",
        janela="diaria",
        data_referencia="2026-10-14",
        percentual_variacao=100.0,
    )
    reg_dia2 = RegistroTopicoOuro(
        id_canal="UC_TIME",
        id_video="consolidado",
        tecnica="kmeans",
        topico="python",
        contagem_atual=15,
        contagem_anterior=10,
        variacao_proporcao=0.5,
        status_tendencia="crescendo",
        comentarios_amostra="Python dia 2",
        janela="diaria",
        data_referencia="2026-10-15",
        percentual_variacao=50.0,
    )

    def mock_carregar(chave: str) -> list[RegistroTopicoOuro]:
        if "2026-10-14" in chave:
            return [reg_dia1]
        elif "2026-10-15" in chave:
            return [reg_dia2]
        return []

    def mock_obter_chave(
        id_canal: str,
        tecnica: str,
        data: str | None = None,
        consolidado: bool = True,
        janela: str = "7dias",
    ) -> str:
        return f"ouro/id_canal={id_canal}/consolidado/tecnica={tecnica}/data={data}/topicos.parquet"

    camada_ouro_mock.obter_chave_tendencias.side_effect = mock_obter_chave
    camada_ouro_mock.carregar_topicos.side_effect = mock_carregar

    app = criar_aplicacao(camada_ouro=camada_ouro_mock)
    cliente = TestClient(app)

    resp = cliente.get("/v1/canais/UC_TIME/topicos/python/serie_temporal?tecnica=kmeans")
    assert resp.status_code == 200
    dados = resp.json()
    assert dados["id_canal"] == "UC_TIME"
    assert dados["topico"] == "python"
    assert dados["tecnica"] == "kmeans"
    assert len(dados["pontos"]) == 2

    p0 = dados["pontos"][0]
    assert p0["data"] == "2026-10-14"
    assert p0["contagem"] == 10
    assert p0["status_tendencia"] == "novo"
    assert p0["percentual_variacao"] == 100.0

    p1 = dados["pontos"][1]
    assert p1["data"] == "2026-10-15"
    assert p1["contagem"] == 15
    assert p1["status_tendencia"] == "crescendo"
    assert p1["percentual_variacao"] == 50.0


