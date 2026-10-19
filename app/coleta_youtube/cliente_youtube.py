"""Cliente HTTP resiliente para integração com a YouTube Data API v3."""

from datetime import datetime, timezone
import hashlib
import time
from typing import Protocol, cast
import requests

from app.coleta_youtube.modelos_coleta import ComentarioColetado, MetadadosVideo
from app.coleta_youtube.tratador_erros import (
    ChaveApiAusenteErro,
    ColetaYouTubeErro,
    ComentariosDesativadosErro,
    QuotaExcedidaErro,
    VideoIndisponivelErro,
)
from app.configuracao_geral.tipos_enumerados import OrigemComentario


class ProtocoloRequisitorHttp(Protocol):
    """Protocolo estrutural para desacoplamento de chamadas HTTP (permitindo mocks em testes)."""

    def get(
        self,
        url: str | bytes,
        *,
        params: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> requests.Response: ...


class ClienteYouTube:
    """Encapsula operações da YouTube Data API com suporte a retries e paginação."""

    _URL_BASE = "https://www.googleapis.com/youtube/v3"

    def __init__(
        self,
        chave_api: str,
        tentativas: int = 4,
        atraso_base_segundos: float = 2.0,
        sessao_http: ProtocoloRequisitorHttp | None = None,
    ) -> None:
        if not chave_api.strip():
            raise ChaveApiAusenteErro(
                "A chave da API do YouTube não pode ser vazia. Defina a variável de ambiente."
            )
        self._chave_api: str = chave_api
        self._tentativas: int = max(1, tentativas)
        self._atraso_base: float = max(0.1, atraso_base_segundos)
        self._sessao: ProtocoloRequisitorHttp = sessao_http or requests.Session()

    def obter_detalhes_canal(self, id_canal: str) -> tuple[str, str]:
        """Obtém o nome do canal e o ID da playlist de uploads via channels.list."""
        url = f"{self._URL_BASE}/channels"
        parametros = {
            "part": "snippet,contentDetails",
            "id": id_canal,
            "key": self._chave_api,
        }
        dados = self._executar_requisicao_com_retry(url, parametros)
        itens = self._extrair_lista(dados, "items")
        if not itens:
            raise VideoIndisponivelErro(f"Canal não encontrado ou sem permissão: {id_canal}")

        primeiro_item = self._converter_para_dicionario(itens[0])
        snippet = self._extrair_dicionario(primeiro_item, "snippet")
        content_details = self._extrair_dicionario(primeiro_item, "contentDetails")
        related_playlists = self._extrair_dicionario(content_details, "relatedPlaylists")

        nome_canal = str(snippet.get("title", id_canal))
        playlist_id = str(related_playlists.get("uploads", ""))
        if not playlist_id:
            raise VideoIndisponivelErro(f"Playlist de uploads não encontrada para o canal {id_canal}")
        return nome_canal, playlist_id

    def obter_id_playlist_uploads(self, id_canal: str) -> str:
        """Obtém o ID da playlist de uploads do canal via channels.list."""
        _, playlist_id = self.obter_detalhes_canal(id_canal)
        return playlist_id

    def listar_videos_recentes(
        self,
        id_canal: str,
        data_limite_iso: datetime,
        limite_videos: int | None = None,
    ) -> list[MetadadosVideo]:
        """Enumera vídeos da playlist de uploads publicados a partir da data limite."""
        playlist_id = self.obter_id_playlist_uploads(id_canal)
        url = f"{self._URL_BASE}/playlistItems"
        videos: list[MetadadosVideo] = []
        token_pagina: str | None = None

        while True:
            parametros = {
                "part": "snippet,contentDetails",
                "playlistId": playlist_id,
                "maxResults": "50",
                "key": self._chave_api,
            }
            if token_pagina:
                parametros["pageToken"] = token_pagina

            dados = self._executar_requisicao_com_retry(url, parametros)
            itens = self._extrair_lista(dados, "items")
            if not itens:
                break

            atingiu_limite_temporal = False
            for item in itens:
                item_dict = self._converter_para_dicionario(item)
                content_details = self._extrair_dicionario(item_dict, "contentDetails")
                snippet = self._extrair_dicionario(item_dict, "snippet")

                id_video = str(content_details.get("videoId", ""))
                titulo = str(snippet.get("title", ""))
                publicado_em_str = str(
                    content_details.get("videoPublishedAt", snippet.get("publishedAt", ""))
                )
                try:
                    publicado_em = self._parse_iso_datetime(publicado_em_str)
                except Exception:
                    continue

                if publicado_em < data_limite_iso:
                    atingiu_limite_temporal = True
                    break

                videos.append(
                    MetadadosVideo(
                        id_video=id_video,
                        id_canal=id_canal,
                        titulo=titulo,
                        publicado_em=publicado_em,
                    )
                )

                if limite_videos and len(videos) >= limite_videos:
                    return videos

            if atingiu_limite_temporal:
                break

            proximo_token = dados.get("nextPageToken")
            if isinstance(proximo_token, str) and proximo_token.strip():
                token_pagina = proximo_token
            else:
                break

        return videos

    def listar_comentarios_principais(
        self,
        id_video: str,
        id_canal: str,
        tamanho_pagina: int = 100,
    ) -> list[ComentarioColetado]:
        """Busca exaustivamente os tópicos de comentários (commentThreads) de um vídeo."""
        url = f"{self._URL_BASE}/commentThreads"
        comentarios: list[ComentarioColetado] = []
        token_pagina: str | None = None
        momento_coleta = datetime.now(timezone.utc)

        while True:
            parametros = {
                "part": "snippet",
                "videoId": id_video,
                "maxResults": str(min(100, max(1, tamanho_pagina))),
                "order": "time",
                "key": self._chave_api,
            }
            if token_pagina:
                parametros["pageToken"] = token_pagina

            try:
                dados = self._executar_requisicao_com_retry(url, parametros)
            except ComentariosDesativadosErro:
                return []

            itens = self._extrair_lista(dados, "items")
            if not itens:
                break

            for item in itens:
                item_dict = self._converter_para_dicionario(item)
                etag = str(item_dict.get("etag", ""))
                id_thread = str(item_dict.get("id", ""))
                snippet_thread = self._extrair_dicionario(item_dict, "snippet")
                top_comment = self._extrair_dicionario(snippet_thread, "topLevelComment")
                top_snippet = self._extrair_dicionario(top_comment, "snippet")

                texto_original = str(top_snippet.get("textOriginal", ""))
                publicado_em = self._parse_iso_datetime(str(top_snippet.get("publishedAt", "")))
                atualizado_em = self._parse_iso_datetime(str(top_snippet.get("updatedAt", "")))
                curtidas = int(str(top_snippet.get("likeCount", 0)))
                hash_conteudo = hashlib.sha256(texto_original.encode("utf-8")).hexdigest()

                comentarios.append(
                    ComentarioColetado(
                        id_comentario=id_thread,
                        id_video=id_video,
                        id_canal=id_canal,
                        id_comentario_pai=None,
                        etag=etag,
                        texto_original=texto_original,
                        hash_conteudo=hash_conteudo,
                        publicado_em=publicado_em,
                        atualizado_em=atualizado_em,
                        contagem_curtidas=curtidas,
                        origem=OrigemComentario.PRINCIPAL,
                        coletado_em=momento_coleta,
                    )
                )

            proximo_token = dados.get("nextPageToken")
            if isinstance(proximo_token, str) and proximo_token.strip():
                token_pagina = proximo_token
            else:
                break

        return comentarios

    def listar_respostas_comentario(
        self,
        id_comentario_pai: str,
        id_video: str,
        id_canal: str,
        tamanho_pagina: int = 100,
    ) -> list[ComentarioColetado]:
        """Busca todas as respostas de um comentário via comments.list(parentId=...)."""
        url = f"{self._URL_BASE}/comments"
        respostas: list[ComentarioColetado] = []
        token_pagina: str | None = None
        momento_coleta = datetime.now(timezone.utc)

        while True:
            parametros = {
                "part": "snippet",
                "parentId": id_comentario_pai,
                "maxResults": str(min(100, max(1, tamanho_pagina))),
                "key": self._chave_api,
            }
            if token_pagina:
                parametros["pageToken"] = token_pagina

            dados = self._executar_requisicao_com_retry(url, parametros)
            itens = self._extrair_lista(dados, "items")
            if not itens:
                break

            for item in itens:
                item_dict = self._converter_para_dicionario(item)
                etag = str(item_dict.get("etag", ""))
                id_resposta = str(item_dict.get("id", ""))
                snippet = self._extrair_dicionario(item_dict, "snippet")

                texto_original = str(snippet.get("textOriginal", ""))
                publicado_em = self._parse_iso_datetime(str(snippet.get("publishedAt", "")))
                atualizado_em = self._parse_iso_datetime(str(snippet.get("updatedAt", "")))
                curtidas = int(str(snippet.get("likeCount", 0)))
                hash_conteudo = hashlib.sha256(texto_original.encode("utf-8")).hexdigest()

                respostas.append(
                    ComentarioColetado(
                        id_comentario=id_resposta,
                        id_video=id_video,
                        id_canal=id_canal,
                        id_comentario_pai=id_comentario_pai,
                        etag=etag,
                        texto_original=texto_original,
                        hash_conteudo=hash_conteudo,
                        publicado_em=publicado_em,
                        atualizado_em=atualizado_em,
                        contagem_curtidas=curtidas,
                        origem=OrigemComentario.RESPOSTA,
                        coletado_em=momento_coleta,
                    )
                )

            proximo_token = dados.get("nextPageToken")
            if isinstance(proximo_token, str) and proximo_token.strip():
                token_pagina = proximo_token
            else:
                break

        return respostas

    def _executar_requisicao_com_retry(
        self,
        url: str,
        parametros: dict[str, str],
    ) -> dict[str, object]:
        """Executa a requisição com backoff exponencial sem expor segredos nos erros."""
        ultimo_erro: Exception | None = None

        for tentativa in range(1, self._tentativas + 1):
            try:
                resposta = self._sessao.get(url, params=parametros, timeout=30.0)
                status = resposta.status_code

                if status == 200:
                    corpo: object = resposta.json()
                    if isinstance(corpo, dict):
                        return cast(dict[str, object], corpo)
                    raise ColetaYouTubeErro("Formato inesperado na resposta da API.")

                if status in (403, 429):
                    msg_erro, motivos = self._extrair_detalhes_erro_api(resposta)
                    if "commentsDisabled" in motivos or "disabled comments" in msg_erro.lower():
                        raise ComentariosDesativadosErro("Comentários desativados no vídeo.")
                    if "quotaExceeded" in motivos or "quota" in msg_erro.lower() or status == 429:
                        raise QuotaExcedidaErro(f"Quota excedida na YouTube API: {msg_erro}")
                    raise QuotaExcedidaErro(f"Acesso negado ou restrição na API: {msg_erro}")

                if status == 404:
                    raise VideoIndisponivelErro("Recurso não encontrado na API do YouTube.")

                resposta.raise_for_status()

            except (QuotaExcedidaErro, ComentariosDesativadosErro, VideoIndisponivelErro):
                raise
            except Exception as erro:
                ultimo_erro = erro
                if tentativa < self._tentativas:
                    tempo_espera = self._atraso_base * (2 ** (tentativa - 1))
                    time.sleep(tempo_espera)

        raise ColetaYouTubeErro(
            f"Falha na comunicação com a YouTube API após {self._tentativas} tentativas: {ultimo_erro}"
        ) from ultimo_erro

    @staticmethod
    def _extrair_detalhes_erro_api(resposta: requests.Response) -> tuple[str, list[str]]:
        """Extrai mensagem e lista de motivos (reasons) do erro da API."""
        mensagem = resposta.text
        reasons: list[str] = []
        try:
            corpo: object = resposta.json()
            if isinstance(corpo, dict):
                corpo_dict = cast(dict[str, object], corpo)
                erro_obj = corpo_dict.get("error")
                if isinstance(erro_obj, dict):
                    erro_dict = cast(dict[str, object], erro_obj)
                    mensagem = str(erro_dict.get("message", mensagem))
                    erros_lista = erro_dict.get("errors")
                    if isinstance(erros_lista, list):
                        lista_obj = cast(list[object], erros_lista)
                        for sub_err in lista_obj:
                            if isinstance(sub_err, dict):
                                sub_dict = cast(dict[str, object], sub_err)
                                reason = sub_dict.get("reason")
                                if isinstance(reason, str):
                                    reasons.append(reason)
        except Exception:
            pass
        return mensagem, reasons

    @staticmethod
    def _parse_iso_datetime(data_str: str) -> datetime:
        """Faz parse de data ISO 8601 suportando o sufixo Z."""
        if not data_str:
            return datetime.now(timezone.utc)
        data_limpa = data_str.replace("Z", "+00:00")
        return datetime.fromisoformat(data_limpa)

    @staticmethod
    def _converter_para_dicionario(item: object) -> dict[str, object]:
        if isinstance(item, dict):
            return cast(dict[str, object], item)
        return {}

    @staticmethod
    def _extrair_dicionario(origem: dict[str, object], chave: str) -> dict[str, object]:
        sub = origem.get(chave)
        if isinstance(sub, dict):
            return cast(dict[str, object], sub)
        return {}

    @staticmethod
    def _extrair_lista(origem: dict[str, object], chave: str) -> list[object]:
        sub = origem.get(chave)
        if isinstance(sub, list):
            return cast(list[object], sub)
        return []
