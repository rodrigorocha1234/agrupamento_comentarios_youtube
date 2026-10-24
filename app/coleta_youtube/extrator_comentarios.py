"""Extrator de alto nível para orquestração da coleta de vídeos e comentários de um canal."""

from datetime import datetime, timedelta, timezone
from app.coleta_youtube.cliente_youtube import ClienteYouTube
from app.coleta_youtube.modelos_coleta import ComentarioColetado, MetadadosVideo


class ExtratorComentarios:
    """Orquestra a coleta incremental completa de um canal respeitando parâmetros configurados."""

    def __init__(self, cliente_youtube: ClienteYouTube) -> None:
        self._cliente: ClienteYouTube = cliente_youtube

    def extrair_canal_completo(
        self,
        id_canal: str,
        dias_retroativos: int = 7,
        incluir_respostas: bool = True,
        limite_videos: int | None = None,
        tamanho_pagina: int = 100,
    ) -> tuple[list[MetadadosVideo], list[ComentarioColetado]]:
        """Executa a coleta de todos os vídeos recentes e seus respectivos comentários e respostas."""
        agora = datetime.now(timezone.utc)
        data_limite = agora - timedelta(days=dias_retroativos)

        videos = self._cliente.listar_videos_recentes(
            id_canal=id_canal,
            data_limite_iso=data_limite,
            limite_videos=limite_videos,
        )

        todos_comentarios: list[ComentarioColetado] = []

        for video in videos:
            comentarios_principais = self._cliente.listar_comentarios_principais(
                id_video=video.id_video,
                id_canal=id_canal,
                tamanho_pagina=tamanho_pagina,
            )
            todos_comentarios.extend(comentarios_principais)

            if incluir_respostas:
                for comentario in comentarios_principais:
                    respostas = self._cliente.listar_respostas_comentario(
                        id_comentario_pai=comentario.id_comentario,
                        id_video=video.id_video,
                        id_canal=id_canal,
                        tamanho_pagina=tamanho_pagina,
                    )
                    todos_comentarios.extend(respostas)

        return videos, todos_comentarios

    def obter_detalhes_canal(self, id_canal: str) -> tuple[str, str]:
        """Recupera nome do canal e playlist uploads delegando ao cliente."""
        return self._cliente.obter_detalhes_canal(id_canal)
