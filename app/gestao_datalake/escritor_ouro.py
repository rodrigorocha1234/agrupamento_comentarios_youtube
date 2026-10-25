"""Escritor tabular e analítico em formato Parquet para a camada Gold do Data Lake."""

import io
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import final

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from app.avaliacao_modelos.metricas_estatisticas import ResultadoAvaliacao
from app.dominio_contratos.protocolos_datalake import ArmazenamentoLake


@final
class EscritorCamadaOuro:
    """Persiste datasets analíticos, métricas de partição e manifestos na camada Gold."""

    def __init__(
        self,
        armazenamento: ArmazenamentoLake,
        prefixo_base: str = "gold/steam",
    ) -> None:
        self._armazenamento = armazenamento
        self._prefixo = prefixo_base.strip("/")

    def construir_caminho_clusters(
        self, appid: int, nome_modelo: str, versao: str
    ) -> str:
        """Gera caminho particionado hierárquico por appid e data corrente."""
        agora = datetime.now(UTC)
        return (
            f"{self._prefixo}/clusters/appid={appid}/ano={agora.year}/"
            f"mes={agora.month:02d}/modelo_{nome_modelo}_{versao}.parquet"
        )

    def construir_caminho_metricas(self, appid: int, versao: str) -> str:
        """Gera caminho para tabela colunar de métricas estatísticas da partição."""
        return f"{self._prefixo}/metricas/appid={appid}/metricas_{versao}.parquet"

    def construir_caminho_resumo(self, appid: int, versao: str) -> str:
        """Gera caminho para o resumo executivo textual ou JSON da partição."""
        return f"{self._prefixo}/resumos/appid={appid}/resumo_executivo_{versao}.json"

    def construir_caminho_manifesto(self, appid: int, versao: str) -> str:
        """Gera caminho para o manifesto de linhagem e integridade analítica."""
        return f"{self._prefixo}/manifestos/appid={appid}/manifesto_{versao}.json"

    def salvar_dataset_clusters(
        self, appid: int, nome_modelo: str, versao: str, df: pd.DataFrame
    ) -> str:
        """Serializa o DataFrame analítico em Parquet Snappy e envia para a camada Gold."""
        if df.empty:
            return ""

        tabela_arrow = pa.Table.from_pandas(df)
        buffer_saida = io.BytesIO()
        pq.write_table(tabela_arrow, buffer_saida, compression="snappy")
        conteudo_bytes = buffer_saida.getvalue()

        caminho_chave = self.construir_caminho_clusters(appid, nome_modelo, versao)
        self._armazenamento.gravar_bytes(caminho_chave, conteudo_bytes)
        return caminho_chave

    def salvar_metricas(
        self, appid: int, versao: str, avaliacao: ResultadoAvaliacao
    ) -> str:
        """Salva métricas estatísticas em arquivo Parquet colunar na camada Gold."""
        dados_metricas: dict[str, list[int | float | None]] = {
            "total_amostras": [avaliacao.total_amostras],
            "total_clusters": [avaliacao.total_clusters],
            "total_ruido": [avaliacao.total_ruido],
            "proporcao_ruido": [avaliacao.proporcao_ruido],
            "silhouette_global": [avaliacao.silhouette_global],
            "silhouette_sem_ruido": [avaliacao.silhouette_sem_ruido],
            "davies_bouldin": [avaliacao.davies_bouldin],
            "calinski_harabasz": [avaliacao.calinski_harabasz],
        }

        tabela_arrow = pa.Table.from_pydict(dados_metricas)
        buffer_saida = io.BytesIO()
        pq.write_table(tabela_arrow, buffer_saida, compression="snappy")
        conteudo_bytes = buffer_saida.getvalue()

        caminho_chave = self.construir_caminho_metricas(appid, versao)
        self._armazenamento.gravar_bytes(caminho_chave, conteudo_bytes)
        return caminho_chave

    def salvar_resumo_executivo(self, appid: int, versao: str, resumo_json: str) -> str:
        """Persiste resumo executivo em formato JSON na camada Gold."""
        caminho_chave = self.construir_caminho_resumo(appid, versao)
        self._armazenamento.gravar_texto(caminho_chave, resumo_json)
        return caminho_chave

    def salvar_manifesto_ouro(
        self, appid: int, versao: str, manifesto_dados: Mapping[str, str | int | float]
    ) -> str:
        """Persiste manifesto de integridade e linhagem da partição Gold."""

        conteudo_texto = json.dumps(manifesto_dados, indent=2, ensure_ascii=False)
        caminho_chave = self.construir_caminho_manifesto(appid, versao)
        self._armazenamento.gravar_texto(caminho_chave, conteudo_texto)
        return caminho_chave
