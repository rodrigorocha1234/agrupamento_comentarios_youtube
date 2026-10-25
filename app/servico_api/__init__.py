"""Módulo do serviço HTTP/REST com FastAPI e métricas operacionais."""

from app.servico_api.aplicacao import criar_aplicacao_fastapi
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

__all__ = [
    "EstadoAplicacao",
    "RequisicaoLote",
    "RequisicaoPonto",
    "RespostaInfoModelo",
    "RespostaPerfilCluster",
    "RespostaPrevisaoLote",
    "RespostaPrevisaoPonto",
    "RespostaProntidao",
    "RespostaResumoClusters",
    "RespostaSaude",
    "criar_aplicacao_fastapi",
]
