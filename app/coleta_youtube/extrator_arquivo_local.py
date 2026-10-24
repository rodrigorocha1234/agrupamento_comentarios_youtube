"""Adaptador (Adapter Pattern) para ingestão de dados a partir de arquivos locais (CSV, Parquet, JSONL)."""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import pandas as pd

from app.coleta_youtube.modelos_coleta import ComentarioColetado, MetadadosVideo
from app.configuracao_geral.modelos_configuracao import ConfiguracaoColeta


class ExtratorArquivoLocal:
    """Implementa ProtocoloExtratorComentarios lendo de arquivos locais tabulares."""

    def __init__(self, config_coleta: ConfiguracaoColeta) -> None:
        self._config: ConfiguracaoColeta = config_coleta
        self._caminho: Path | None = (
            Path(config_coleta.caminho_dados) if config_coleta.caminho_dados else None
        )
        self._col_texto: str = config_coleta.coluna_texto
        self._col_id: str = config_coleta.coluna_id
        self._col_tempo: str | None = config_coleta.coluna_temporal

    def extrair_canal_completo(
        self,
        id_canal: str,
        dias_retroativos: int = 7,
        incluir_respostas: bool = True,
        limite_videos: int | None = None,
        tamanho_pagina: int = 100,
    ) -> tuple[list[MetadadosVideo], list[ComentarioColetado]]:
        """Lê os registros do arquivo local e mapeia para o esquema padrão do pipeline."""
        if not self._caminho or not self._caminho.exists():
            return [], []

        extensao = self._caminho.suffix.lower()
        if extensao == ".csv":
            df = pd.read_csv(self._caminho)
        elif extensao in [".parquet", ".pq"]:
            df = pd.read_parquet(self._caminho)
        elif extensao in [".jsonl", ".json"]:
            df = pd.read_json(self._caminho, lines=extensao == ".jsonl")
        else:
            df = pd.read_csv(self._caminho)

        if df.empty:
            return [], []

        # Determina colunas disponíveis
        colunas_df = list(df.columns)
        col_txt = self._col_texto if self._col_texto in colunas_df else str(colunas_df[0])
        col_id = self._col_id if self._col_id in colunas_df else None

        agora = datetime.now(timezone.utc)
        comentarios: list[ComentarioColetado] = []
        videos_map: dict[str, MetadadosVideo] = {}

        registros: list[dict[str, object]] = df.to_dict(orient="records")
        for idx, row in enumerate(registros):
            cid = str(row.get(col_id, f"local_{idx}")) if col_id else f"local_{idx}"
            vid = str(row.get("id_video", f"lote_{id_canal}"))
            raw_txt = row.get(col_txt, "")
            texto = str(raw_txt) if raw_txt is not None else ""

            # Data temporal
            data_pub = agora
            if self._col_tempo and self._col_tempo in row:
                val_tempo = row[self._col_tempo]
                if val_tempo is not None and str(val_tempo).strip():
                    try:
                        ts = pd.to_datetime(str(val_tempo))
                        data_convertida = ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else agora
                        data_pub = (
                            data_convertida.replace(tzinfo=timezone.utc)
                            if data_convertida.tzinfo is None
                            else data_convertida
                        )
                    except Exception:
                        data_pub = agora

            hash_val = hashlib.sha256(texto.encode("utf-8")).hexdigest()

            if vid not in videos_map:
                videos_map[vid] = MetadadosVideo(
                    id_video=vid,
                    id_canal=id_canal,
                    titulo=f"Vídeo/Lote {vid}",
                    publicado_em=data_pub,
                )

            curtidas_raw = row.get("curtidas", 0)
            curtidas_int = int(str(curtidas_raw)) if curtidas_raw is not None and str(curtidas_raw).isdigit() else 0

            comentarios.append(
                ComentarioColetado(
                    id_comentario=cid,
                    id_video=vid,
                    id_canal=id_canal,
                    id_comentario_pai=None,
                    etag=hash_val[:12],
                    texto_original=texto,
                    hash_conteudo=hash_val,
                    publicado_em=data_pub,
                    atualizado_em=data_pub,
                    contagem_curtidas=curtidas_int,
                    origem="principal",
                    coletado_em=agora,
                )
            )

        videos = list(videos_map.values())
        if limite_videos and len(videos) > limite_videos:
            videos = videos[:limite_videos]
            ids_permitidos = {v.id_video for v in videos}
            comentarios = [c for c in comentarios if c.id_video in ids_permitidos]

        return videos, comentarios

    def obter_detalhes_canal(self, id_canal: str) -> tuple[str, str]:
        """Devolve o nome do canal correspondente à fonte de arquivo local."""
        return f"Fonte Local ({id_canal})", "local_uploads"
