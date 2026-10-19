"""Hierarquia de exceções de domínio em português para a etapa de coleta do YouTube."""


class ColetaYouTubeErro(Exception):
    """Exceção base para falhas durante a coleta do YouTube."""


class QuotaExcedidaErro(ColetaYouTubeErro):
    """Levantada quando a quota da API do YouTube é excedida (HTTP 403/429)."""


class ComentariosDesativadosErro(ColetaYouTubeErro):
    """Levantada quando os comentários do vídeo estão desativados (commentsDisabled)."""


class VideoIndisponivelErro(ColetaYouTubeErro):
    """Levantada quando o vídeo não foi encontrado ou está privado."""


class ChaveApiAusenteErro(ColetaYouTubeErro):
    """Levantada quando a chave da API do YouTube não foi informada via variável de ambiente."""
