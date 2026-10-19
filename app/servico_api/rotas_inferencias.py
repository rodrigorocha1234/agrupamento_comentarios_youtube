"""Rotas da API para inferência em tempo real via MLflow Serving Adapter."""

from fastapi import APIRouter, HTTPException, Request

from app.integracao_mlflow.adaptador_serving import (
    AdaptadorServing,
    AdaptadorServingErro,
)
from app.servico_api.esquemas_respostas import (
    RequisicaoInferencia,
    RespostaInferencia,
)

roteador_inferencias = APIRouter(prefix="/v1/inferencias", tags=["inferencias"])


@roteador_inferencias.post("", response_model=RespostaInferencia)
def executar_inferencia(
    requisicao: RequisicaoInferencia,
    request: Request,
) -> RespostaInferencia:
    """Envia textos para o serving do modelo registrado e retorna predições de cluster."""
    adaptador: AdaptadorServing | None = getattr(request.app.state, "adaptador_serving", None)
    if adaptador is None:
        raise HTTPException(
            status_code=500, detail="Adaptador de serving não configurado na aplicação."
        )

    try:
        predicoes = adaptador.invocar_predicao(requisicao.textos)
    except AdaptadorServingErro as erro:
        raise HTTPException(status_code=502, detail=f"Erro no serviço de inferência: {erro}") from erro

    return RespostaInferencia(
        predicoes=predicoes,
        total_amostras=len(predicoes),
    )
