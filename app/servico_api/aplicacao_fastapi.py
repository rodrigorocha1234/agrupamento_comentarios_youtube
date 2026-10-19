"""Aplicação principal FastAPI com roteadores e injeção de dependências."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from app.coleta_youtube.cliente_youtube import ClienteYouTube
from app.configuracao_geral.modelos_configuracao import ConfiguracaoGlobal
from app.gestao_dados.camada_ouro import CamadaOuro
from app.integracao_mlflow.adaptador_serving import AdaptadorServing
from app.servico_api.rotas_canais import roteador_canais
from app.servico_api.rotas_inferencias import roteador_inferencias
from app.servico_api.rotas_videos import roteador_videos


def criar_aplicacao(
    camada_ouro: CamadaOuro | None = None,
    adaptador_serving: AdaptadorServing | None = None,
    cliente_youtube: ClienteYouTube | None = None,
    configuracao_global: ConfiguracaoGlobal | None = None,
) -> FastAPI:
    """Fábrica de inicialização da aplicação FastAPI."""
    app = FastAPI(
        title="API de Agrupamento de Comentários do YouTube",
        version="0.1.0",
        description="Consultas analíticas de tendências, clusters e inferências MLOps.",
    )

    # Carrega configuração global se não injetada
    cfg: ConfiguracaoGlobal | None = configuracao_global
    if cfg is None:
        try:
            import os
            from pathlib import Path
            from app.configuracao_geral.provedor_configuracao import ProvedorConfiguracao

            caminho_cfg = Path(os.getenv("CONFIG_PATH", "config/entradas.yaml"))
            if caminho_cfg.exists():
                cfg = ProvedorConfiguracao(caminho_cfg).carregar()
        except Exception:
            pass

    # Inicialização automática caso não injetadas manualmente (ex: execução via CLI ou container)
    if camada_ouro is None and cfg is not None:
        try:
            import os
            from app.gestao_dados.cliente_s3 import ClienteS3

            endpoint_s3 = os.getenv(cfg.persistencia.endpoint_env, "http://storage:9000")
            access_key = os.getenv(cfg.persistencia.access_key_env, "s3admin")
            secret_key = os.getenv(cfg.persistencia.secret_key_env, "s3admin")
            s3 = ClienteS3(endpoint_url=endpoint_s3, access_key=access_key, secret_key=secret_key)
            camada_ouro = CamadaOuro(
                s3,
                bucket=cfg.persistencia.bucket,
                prefixo_ouro=cfg.persistencia.prefixo_ouro,
                padrao_chave_video=cfg.persistencia.padrao_chave_ouro_video,
                padrao_chave_consolidado=cfg.persistencia.padrao_chave_ouro_consolidado,
            )
            from app.coleta_metricas.medidor_datalake import MedidorDatalake
            MedidorDatalake.sincronizar_metricas_existentes(s3, cfg.persistencia.bucket)
        except Exception:
            pass

    if adaptador_serving is None and cfg is not None:
        try:
            import os

            url_serving = os.getenv(cfg.mlflow.serving_url_env, "http://mlflow-serving:8080")
            adaptador_serving = AdaptadorServing(serving_url=url_serving)
        except Exception:
            pass

    if cliente_youtube is None:
        try:
            import os
            from pathlib import Path

            chave_yt = os.getenv("YOUTUBE_API_KEY", "")
            if not chave_yt:
                caminho_env = Path(".env")
                if caminho_env.exists():
                    for linha in caminho_env.read_text(encoding="utf-8").splitlines():
                        if linha.startswith("YOUTUBE_API_KEY="):
                            chave_yt = linha.split("=", 1)[1].strip().strip('"').strip("'")
            if chave_yt:
                cliente_youtube = ClienteYouTube(chave_api=chave_yt)
        except Exception:
            pass

    # Habilita CORS se configurado
    if cfg is not None and cfg.api.cors_origens:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cfg.api.cors_origens,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Injeção de dependências no state
    app.state.camada_ouro = camada_ouro
    app.state.adaptador_serving = adaptador_serving
    app.state.cliente_youtube = cliente_youtube
    app.state.configuracao_global = cfg

    # Inclusão de roteadores
    app.include_router(roteador_canais)
    app.include_router(roteador_videos)
    app.include_router(roteador_inferencias)

    # Anexa middleware Prometheus e endpoint /metrics
    from app.coleta_metricas.middleware_prometheus import anexar_observabilidade_fastapi
    from app.configuracao_geral.tipos_enumerados import StatusSaude
    anexar_observabilidade_fastapi(app)

    @app.get("/health", tags=["sistema"])
    def checagem_saude() -> JSONResponse:
        return JSONResponse(content={"status": StatusSaude.SAUDAVEL, "versao": "0.1.0"})

    @app.get("/documentacao", include_in_schema=False)
    def exibir_documentacao() -> HTMLResponse:
        from pathlib import Path

        caminho_doc = Path("docs/index.html")
        if caminho_doc.exists():
            return HTMLResponse(content=caminho_doc.read_text(encoding="utf-8"))
        return HTMLResponse(content="<h1>Documentação não encontrada</h1>", status_code=404)

    return app
