"""Pacote de coleta incremental da YouTube Data API."""

from app.coleta_youtube.cliente_youtube import ClienteYouTube
from app.coleta_youtube.extrator_comentarios import ExtratorComentarios
from app.coleta_youtube.modelos_coleta import ComentarioColetado, MetadadosVideo
from app.coleta_youtube.tratador_erros import (
    ChaveApiAusenteErro,
    ColetaYouTubeErro,
    ComentariosDesativadosErro,
    QuotaExcedidaErro,
    VideoIndisponivelErro,
)

from app.coleta_youtube.extrator_arquivo_local import ExtratorArquivoLocal
from app.coleta_youtube.fabrica_fontes import FabricaFontesDados

__all__ = [
    "ChaveApiAusenteErro",
    "ClienteYouTube",
    "ColetaYouTubeErro",
    "ComentarioColetado",
    "ComentariosDesativadosErro",
    "ExtratorComentarios",
    "ExtratorArquivoLocal",
    "FabricaFontesDados",
    "MetadadosVideo",
    "QuotaExcedidaErro",
    "VideoIndisponivelErro",
]
