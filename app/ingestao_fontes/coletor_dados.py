"""Orquestrador agnóstico de coleta incremental e despacho para o Data Lakehouse remoto."""

import time
from typing import Final

import pandas as pd

from app.contratos.fonte_dados import ProtocoloFonteDados
from app.contratos.repositorio import ProtocoloRepositorioLakehouse

COLUNAS_NUMERICAS_PADRAO: Final[list[str]] = [
    "votes_up",
    "votes_funny",
    "weighted_vote_score",
    "comment_count",
    "num_reviews",
    "playtime_forever",
    "playtime_last_two_weeks",
    "playtime_at_review",
]


class ColetorDados:
    """Orquestra a coleta incremental de dados a partir de qualquer fonte e persiste no Data Lakehouse."""

    def __init__(
        self,
        fonte: ProtocoloFonteDados,
        repositorio: ProtocoloRepositorioLakehouse,
        campo_deduplicacao: str = "recommendationid",
    ) -> None:
        self._fonte = fonte
        self._repositorio = repositorio
        self._campo_deduplicacao = campo_deduplicacao

    def executar_coleta(
        self,
        identificador_origem: str | int,
        marcador_inicial: str | None = None,
        limite_total_registros: int = 1000,
        tamanho_lote: int = 100,
        pausa_entre_lotes_segundos: float = 0.2,
    ) -> dict[str, object]:
        """Executa a coleta paginada persistindo lotes na Bronze e consolidado na Silver.

        Args:
            identificador_origem: Identificador do recurso a coletar (ex: AppID, tabela SQL).
            marcador_inicial: Cursor ou offset inicial ('*' para primeira página).
            limite_total_registros: Limite máximo acumulado de registros a extrair.
            tamanho_lote: Tamanho máximo de cada requisição individual.
            pausa_entre_lotes_segundos: Intervalo de cortesia entre requisições para evitar rate-limits.

        Retorna:
            Dicionário com métricas de execução e a URI da camada Silver persistida.
        """
        inicio_execucao = time.time()
        marcador_atual = marcador_inicial
        todos_registros: list[dict[str, object]] = []
        chaves_vistas: set[str] = set()
        duplicatas_ignoradas = 0

        uris_bronze: list[str] = []

        while len(todos_registros) < limite_total_registros:
            limite_requisicao = min(tamanho_lote, limite_total_registros - len(todos_registros))
            registros_lote, proximo_marcador, tem_mais = self._fonte.extrair_lote(
                identificador_origem=identificador_origem,
                marcador_posicao=marcador_atual,
                limite=limite_requisicao,
            )

            if not registros_lote:
                break

            # 1. Persistência imediata e imutável do lote bruto na camada Bronze (RustFS/S3)
            uri_bronze = self._repositorio.gravar_bronze(identificador_origem, registros_lote)
            if uri_bronze:
                uris_bronze.append(uri_bronze)

            # 2. Deduplicação em memória para consolidação na camada Silver
            for item in registros_lote:
                chave_item = str(item.get(self._campo_deduplicacao, ""))
                if chave_item and chave_item in chaves_vistas:
                    duplicatas_ignoradas += 1
                    continue

                if chave_item:
                    chaves_vistas.add(chave_item)
                todos_registros.append(item)

            if not tem_mais or not proximo_marcador or proximo_marcador == marcador_atual:
                marcador_atual = proximo_marcador
                break

            marcador_atual = proximo_marcador
            if pausa_entre_lotes_segundos > 0:
                time.sleep(pausa_entre_lotes_segundos)

        # 3. Consolidação e normalização dos dados na camada Silver
        uri_silver = ""
        if todos_registros:
            df_silver = self._normalizar_dataframe_silver(todos_registros)
            uri_silver = self._repositorio.gravar_silver(identificador_origem, df_silver)

        duracao = time.time() - inicio_execucao

        return {
            "identificador_origem": identificador_origem,
            "total_coletado": len(todos_registros),
            "duplicatas_ignoradas": duplicatas_ignoradas,
            "ultimo_marcador": marcador_atual,
            "lotes_bronze_gravados": len(uris_bronze),
            "uri_silver": uri_silver,
            "duracao_segundos": duracao,
        }

    def _normalizar_dataframe_silver(self, registros: list[dict[str, object]]) -> pd.DataFrame:
        """Converte dicionários brutos em DataFrame tipado para a camada Silver."""
        df = pd.DataFrame(registros)

        if self._campo_deduplicacao in df.columns:
            df = df.drop_duplicates(subset=[self._campo_deduplicacao]).copy()

        # Normaliza colunas numéricas com preenchimento seguro de nulos
        for coluna in COLUNAS_NUMERICAS_PADRAO:
            if coluna in df.columns:
                valores = pd.to_numeric(df[coluna], errors="coerce")
                if isinstance(valores, pd.Series):
                    df[coluna] = valores.fillna(0.0)

        # Normaliza colunas booleanas
        if "voted_up" in df.columns:
            df["voted_up"] = df["voted_up"].astype(bool)

        return df
