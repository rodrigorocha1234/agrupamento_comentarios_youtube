"""Escritor tabular normalizado em formato Parquet para a camada Silver do Data Lake."""

import io
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import final

import pyarrow as pa
import pyarrow.parquet as pq

from app.dominio_contratos.modelos_dados import ReviewSteam
from app.dominio_contratos.protocolos_datalake import ArmazenamentoLake


@final
class EscritorCamadaPrata:
    """Normaliza e persiste avaliações em arquivos colunares Parquet."""

    def __init__(
        self,
        armazenamento: ArmazenamentoLake,
        prefixo_base: str = "silver/steam/reviews",
    ) -> None:
        self._armazenamento = armazenamento
        self._prefixo = prefixo_base.strip("/")

    def construir_caminho_particao(self, appid: int, identificador_lote: str) -> str:
        """Gera caminho particionado temporal por appid e data corrente."""
        agora = datetime.now(UTC)
        return (
            f"{self._prefixo}/appid={appid}/ano={agora.year}/"
            f"mes={agora.month:02d}/lote_{identificador_lote}.parquet"
        )

    def salvar_lote_parquet(
        self, appid: int, identificador_lote: str, reviews: Sequence[ReviewSteam]
    ) -> str:
        """Serializa a sequência de reviews para Parquet e envia ao Lakehouse."""
        if not reviews:
            return ""

        dados_tabela = {
            "appid": [r.appid for r in reviews],
            "recommendationid": [r.recommendationid for r in reviews],
            "steamid": [r.author.steamid for r in reviews],
            "language": [r.language for r in reviews],
            "timestamp_created": [r.timestamp_created for r in reviews],
            "timestamp_updated": [r.timestamp_updated for r in reviews],
            "voted_up": [r.voted_up for r in reviews],
            "votes_up": [r.votes_up for r in reviews],
            "votes_funny": [r.votes_funny for r in reviews],
            "weighted_vote_score": [r.weighted_vote_score for r in reviews],
            "comment_count": [r.comment_count for r in reviews],
            "steam_purchase": [r.steam_purchase for r in reviews],
            "received_for_free": [r.received_for_free for r in reviews],
            "written_during_early_access": [
                r.written_during_early_access for r in reviews
            ],
            "primarily_steam_deck": [r.primarily_steam_deck for r in reviews],
            "playtime_forever": [r.author.playtime_forever for r in reviews],
            "playtime_last_two_weeks": [
                r.author.playtime_last_two_weeks for r in reviews
            ],
            "playtime_at_review": [r.author.playtime_at_review for r in reviews],
            "last_played": [r.author.last_played for r in reviews],
            "num_games_owned": [r.author.num_games_owned for r in reviews],
            "num_reviews": [r.author.num_reviews for r in reviews],
        }

        tabela_arrow = pa.Table.from_pydict(dados_tabela)
        buffer_saida = io.BytesIO()
        pq.write_table(tabela_arrow, buffer_saida, compression="snappy")
        conteudo_bytes = buffer_saida.getvalue()

        caminho_chave = self.construir_caminho_particao(appid, identificador_lote)
        self._armazenamento.gravar_bytes(caminho_chave, conteudo_bytes)
        return caminho_chave
