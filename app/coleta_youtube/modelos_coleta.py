"""Modelos de dados tipados para a coleta incremental do YouTube."""

from dataclasses import dataclass
from datetime import datetime

from app.configuracao_geral.tipos_enumerados import OrigemComentario


@dataclass(frozen=True, slots=True)
class MetadadosVideo:
    """Representação de um vídeo coletado."""

    id_video: str
    id_canal: str
    titulo: str
    publicado_em: datetime


@dataclass(frozen=True, slots=True)
class ComentarioColetado:
    """Representação tipada de um comentário ou resposta com minimização de dados pessoais."""

    id_comentario: str
    id_video: str
    id_canal: str
    id_comentario_pai: str | None
    etag: str
    texto_original: str
    hash_conteudo: str
    publicado_em: datetime
    atualizado_em: datetime
    contagem_curtidas: int
    origem: OrigemComentario | str
    coletado_em: datetime

