"""Escritor analítico em formato Parquet para a camada Gold do Lakehouse."""

import io
from typing import final

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from app.dominio_contratos.protocolos_datalake import ArmazenamentoLake


@final
class EscritorCamadaOuro:
    """Persiste datasets rotulados e agregados analíticos da camada Gold no Data Lake."""

    def __init__(
        self,
        armazenamento: ArmazenamentoLake,
        prefixo_base: str = "gold/steam",
    ) -> None:
        self._armazenamento = armazenamento
        self._prefixo = prefixo_base.strip("/")

    def construir_caminho_clusters(self, appid: int, versao: str) -> str:
        """Gera o caminho particionado para o dataset completo rotulado."""
        return f"{self._prefixo}/clusters/appid={appid}/versao={versao}/dados_clusters.parquet"

    def construir_caminho_agregados(self, appid: int, versao: str) -> str:
        """Gera o caminho particionado para a tabela de resumo analítico."""
        return f"{self._prefixo}/agregados/appid={appid}/versao={versao}/resumo_clusters.parquet"

    def salvar_dataset_clusters(
        self, appid: int, versao: str, dados_gold: pd.DataFrame
    ) -> str:
        """Serializa o DataFrame Gold em Parquet Snappy e persiste no armazenamento."""
        if dados_gold.empty:
            return ""

        tabela_arrow = pa.Table.from_pandas(dados_gold, preserve_index=False)
        buffer_saida = io.BytesIO()
        pq.write_table(tabela_arrow, buffer_saida, compression="snappy")
        conteudo_bytes = buffer_saida.getvalue()

        caminho_chave = self.construir_caminho_clusters(appid, versao)
        self._armazenamento.gravar_bytes(caminho_chave, conteudo_bytes)
        return caminho_chave

    def salvar_resumo_clusters(
        self, appid: int, versao: str, resumo_agregado: pd.DataFrame
    ) -> str:
        """Persiste a tabela agregada resumida de clusters em Parquet."""
        if resumo_agregado.empty:
            return ""

        tabela_arrow = pa.Table.from_pandas(resumo_agregado, preserve_index=False)
        buffer_saida = io.BytesIO()
        pq.write_table(tabela_arrow, buffer_saida, compression="snappy")
        conteudo_bytes = buffer_saida.getvalue()

        caminho_chave = self.construir_caminho_agregados(appid, versao)
        self._armazenamento.gravar_bytes(caminho_chave, conteudo_bytes)
        return caminho_chave

    def gerar_tabela_resumo(
        self,
        dados_gold: pd.DataFrame,
        coluna_cluster: str = "cluster_id",
    ) -> pd.DataFrame:
        """Gera um DataFrame tabular resumido com métricas de negócio por cluster."""
        if coluna_cluster not in dados_gold.columns or dados_gold.empty:
            return pd.DataFrame()

        linhas_resumo: list[dict[str, object]] = []
        clusters_unicos = sorted(dados_gold[coluna_cluster].unique())
        total_geral = float(len(dados_gold))

        for c_id in clusters_unicos:
            cluster_int = int(c_id)
            sub = pd.DataFrame(dados_gold.loc[dados_gold[coluna_cluster] == cluster_int])
            total_membros = len(sub)
            prop = (float(total_membros) / total_geral * 100.0) if total_geral > 0 else 0.0

            # Horas jogadas
            if "horas_jogadas_total" in sub.columns:
                arr_h = np.asarray(
                    pd.to_numeric(sub["horas_jogadas_total"], errors="coerce").dropna().values,
                    dtype=np.float64,
                )
                mediana_h = float(np.median(arr_h)) if len(arr_h) > 0 else 0.0
                media_h = float(np.mean(arr_h)) if len(arr_h) > 0 else 0.0
            else:
                mediana_h = 0.0
                media_h = 0.0

            # Positividade
            if "voted_up" in sub.columns and total_membros > 0:
                arr_v = np.asarray(sub["voted_up"].to_numpy(), dtype=np.bool_)
                pos_pct = float(np.sum(arr_v)) / float(len(arr_v)) * 100.0
            else:
                pos_pct = 0.0

            # Rótulo de negócio
            rotulo = (
                str(sub["rotulo_negocio"].iloc[0])
                if "rotulo_negocio" in sub.columns and not sub.empty
                else "padrao"
            )

            linhas_resumo.append(
                {
                    "cluster_id": cluster_int,
                    "rotulo_negocio": rotulo,
                    "total_membros": total_membros,
                    "proporcao_percentual": round(prop, 2),
                    "mediana_horas_jogadas": round(mediana_h, 2),
                    "media_horas_jogadas": round(media_h, 2),
                    "taxa_positividade": round(pos_pct, 2),
                }
            )

        return pd.DataFrame(linhas_resumo)
