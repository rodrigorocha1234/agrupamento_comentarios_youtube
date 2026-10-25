"""Orquestrador de exportação de dados analíticos para a camada Gold e telemetria."""

import json
from datetime import UTC, datetime
from typing import final

import pandas as pd

from app.avaliacao_modelos.metricas_estatisticas import ResultadoAvaliacao
from app.gestao_datalake.escritor_ouro import EscritorCamadaOuro
from app.observabilidade_metricas.telemetria_analitica import TelemetriaAnalitica
from app.visualizacao_dados.painel_executivo import PainelExecutivo


@final
class ExportadorCamadaOuro:
    """Coordena a persistência analítica no Lakehouse, emissão de telemetria e relatórios EDA."""

    def __init__(
        self,
        escritor_ouro: EscritorCamadaOuro,
        telemetria_analitica: TelemetriaAnalitica | None = None,
        painel_executivo: PainelExecutivo | None = None,
    ) -> None:
        self._escritor = escritor_ouro
        self._telemetria = telemetria_analitica
        self._painel = painel_executivo or PainelExecutivo()

    def exportar_camada_ouro(
        self,
        appid: int,
        nome_algoritmo: str,
        versao: str,
        dados_gold: pd.DataFrame,
        avaliacao: ResultadoAvaliacao,
        mapa_rotulos_negocio: dict[int, str] | None = None,
        hash_execucao: str = "",
    ) -> dict[str, str]:
        """Materializa datasets Gold, telemetria Prometheus, manifestos e relatórios executivos."""
        if dados_gold.empty:
            raise ValueError(
                "Não é possível exportar um DataFrame vazio para a camada Gold."
            )

        rotulos_map = mapa_rotulos_negocio or {}

        # 1. Persistência Parquet colunar de clusters
        caminho_clusters = self._escritor.salvar_dataset_clusters(
            appid=appid,
            nome_modelo=nome_algoritmo,
            versao=versao,
            df=dados_gold,
        )
        if self._telemetria is not None:
            self._telemetria.registrar_gravacao_gold(appid, "clusters_parquet")

        # 2. Persistência Parquet de métricas estatísticas da partição
        caminho_metricas = self._escritor.salvar_metricas(
            appid=appid,
            versao=versao,
            avaliacao=avaliacao,
        )
        if self._telemetria is not None:
            self._telemetria.registrar_gravacao_gold(appid, "metricas_parquet")

        # 3. Geração e persistência do resumo executivo em JSON
        resumo_dict: dict[str, str | int | float | dict[str, str]] = {
            "appid": appid,
            "nome_algoritmo": nome_algoritmo,
            "versao": versao,
            "total_amostras": avaliacao.total_amostras,
            "total_clusters": avaliacao.total_clusters,
            "proporcao_ruido": avaliacao.proporcao_ruido,
            "silhouette_global": avaliacao.silhouette_global or 0.0,
            "mapa_personas": {str(k): v for k, v in rotulos_map.items()},
        }
        resumo_json = json.dumps(resumo_dict, indent=2, ensure_ascii=False)
        caminho_resumo = self._escritor.salvar_resumo_executivo(
            appid=appid,
            versao=versao,
            resumo_json=resumo_json,
        )
        if self._telemetria is not None:
            self._telemetria.registrar_gravacao_gold(appid, "resumo_json")

        # 4. Geração e persistência do manifesto de integridade e linhagem
        manifesto_dados: dict[str, str | int | float] = {
            "appid": appid,
            "nome_algoritmo": nome_algoritmo,
            "versao": versao,
            "total_amostras": avaliacao.total_amostras,
            "total_clusters": avaliacao.total_clusters,
            "hash_execucao": hash_execucao,
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
        caminho_manifesto = self._escritor.salvar_manifesto_ouro(
            appid=appid,
            versao=versao,
            manifesto_dados=manifesto_dados,
        )
        if self._telemetria is not None:
            self._telemetria.registrar_gravacao_gold(appid, "manifesto_json")

        # 5. Atualização de Gauges analíticos no Prometheus
        if self._telemetria is not None:
            self._telemetria.registrar_metricas_cluster(
                appid=appid,
                algoritmo=nome_algoritmo,
                avaliacao=avaliacao,
            )

        # 6. Geração do relatório executivo em Markdown
        relatorio_markdown = self._painel.compilar_relatorio_markdown(
            metricas=avaliacao,
            nome_algoritmo=nome_algoritmo,
            mapa_rotulos_negocio=rotulos_map,
            dados_gold=dados_gold,
        )

        return {
            "clusters_parquet": caminho_clusters,
            "metricas_parquet": caminho_metricas,
            "resumo_json": caminho_resumo,
            "manifesto_json": caminho_manifesto,
            "relatorio_markdown": relatorio_markdown,
        }
