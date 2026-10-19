"""Middleware HTTP para exposição de métricas Prometheus na FastAPI."""

import time
from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

CONTADOR_HTTP_REQUISICOES = Counter(
    "youtube_api_requisicoes_total",
    "Total de requisições HTTP processadas pela API",
    ["metodo", "rota", "status_codigo"],
)

HISTOGRAMA_HTTP_LATENCIA = Histogram(
    "youtube_api_latencia_segundos",
    "Latência de atendimento das requisições HTTP em segundos",
    ["metodo", "rota"],
)


class MiddlewarePrometheus(BaseHTTPMiddleware):
    """Intercepta requisições HTTP e registra latência e contadores de status."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        metodo = request.method
        rota = request.url.path
        # Agrupa rotas parametrizadas para evitar explosão de cardinalidade
        if "/videos/" in rota and "/topicos/" in rota:
            rota_agrupada = "/v1/canais/{canal}/videos/{video}/topicos/{topico}/comentarios"
        elif "/videos/" in rota:
            rota_agrupada = "/v1/canais/{canal}/videos/{video}/" + rota.split("/")[-1]
        elif "/canais/" in rota:
            rota_agrupada = "/v1/canais/{canal}/tendencias"
        else:
            rota_agrupada = rota

        inicio = time.perf_counter()
        resposta = await call_next(request)
        duracao = time.perf_counter() - inicio
        status = str(resposta.status_code)

        CONTADOR_HTTP_REQUISICOES.labels(
            metodo=metodo,
            rota=rota_agrupada,
            status_codigo=status,
        ).inc()

        HISTOGRAMA_HTTP_LATENCIA.labels(
            metodo=metodo,
            rota=rota_agrupada,
        ).observe(duracao)

        return resposta


def anexar_observabilidade_fastapi(app: FastAPI) -> None:
    """Registra o middleware e adiciona a rota padrão /metrics à aplicação."""
    app.add_middleware(MiddlewarePrometheus)

    @app.get("/metrics", tags=["observabilidade"], include_in_schema=False)
    def obter_metricas() -> Response:
        conteudo = generate_latest()
        return Response(content=conteudo, media_type=CONTENT_TYPE_LATEST)
