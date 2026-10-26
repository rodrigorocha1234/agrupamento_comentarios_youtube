"""Processador e agregador da dinâmica temporal dos agrupamentos."""

import pandas as pd

from app.analise_clusters.analisador_clusters import ROTULO_RUIDO
from app.analise_temporal.contratos import (
    PontoTemporalCluster,
    ResumoAnaliseTemporal,
)
from app.analise_temporal.detector_anomalias import DetectorAnomaliasTemporais
from app.analise_temporal.estrategia_agregacao import (
    AgregadorMensal,
    EstrategiaAgregacaoTemporal,
)
from app.conf_yaml import ConfigAnaliseTemporalInfo


class AnalisadorTemporalClusters:
    """Orquestra a agregação temporal e a identificação de comportamentos atípicos por cluster."""

    def __init__(
        self,
        estrategia: EstrategiaAgregacaoTemporal | None = None,
        detector: DetectorAnomaliasTemporais | None = None,
        config: ConfigAnaliseTemporalInfo | None = None,
    ) -> None:
        self._config = config or ConfigAnaliseTemporalInfo()
        self._estrategia = estrategia or AgregadorMensal()
        self._detector = detector or DetectorAnomaliasTemporais(self._config.deteccao_picos)

    def analisar(
        self,
        dados: pd.DataFrame,
        rotulos: list[int],
    ) -> ResumoAnaliseTemporal:
        """Gera o sumário temporal a partir dos dados limpos e dos rótulos de agrupamento."""
        coluna_tempo = self._config.coluna_referencia

        if dados.empty or len(rotulos) == 0 or coluna_tempo not in dados.columns:
            return ResumoAnaliseTemporal(
                pontos_temporais=[],
                periodos_ordenados=[],
                clusters_presentes=[],
                alertas_picos=[],
                granularidade=self._estrategia.obter_nome_granularidade(),
                coluna_temporal=coluna_tempo,
                total_amostras_temporais=0,
            )

        df = dados.copy()
        tamanho = min(len(df), len(rotulos))
        df = df.iloc[:tamanho].copy()
        df["_cluster_id"] = rotulos[:tamanho]

        # Normaliza períodos temporais
        df["_periodo"] = self._estrategia.normalizar_periodos(df[coluna_tempo])

        # Remove períodos inválidos
        df_validos = df[df["_periodo"] != "Desconhecido"]
        if df_validos.empty:
            return ResumoAnaliseTemporal(
                pontos_temporais=[],
                periodos_ordenados=[],
                clusters_presentes=sorted(set(rotulos)),
                alertas_picos=[],
                granularidade=self._estrategia.obter_nome_granularidade(),
                coluna_temporal=coluna_tempo,
                total_amostras_temporais=0,
            )

        periodos_unicos = sorted(df_validos["_periodo"].unique().tolist())
        clusters_unicos = sorted(df_validos["_cluster_id"].unique().tolist())

        # Totais por período para cálculo de proporções
        totais_por_periodo: dict[str, int] = df_validos.groupby("_periodo").size().to_dict()

        coluna_voto = "voted_up" if "voted_up" in df_validos.columns else None
        coluna_horas = (
            "playtime_forever"
            if "playtime_forever" in df_validos.columns
            else ("author_playtime_forever" if "author_playtime_forever" in df_validos.columns else None)
        )

        pontos_map: dict[tuple[str, int], PontoTemporalCluster] = {}

        # Agrupamento por período e cluster
        grupos = df_validos.groupby(["_periodo", "_cluster_id"])
        for (periodo, cid), grupo in grupos:
            periodo_str = str(periodo)
            cid_int = int(cid)
            qtd = len(grupo)
            total_periodo = totais_por_periodo.get(periodo_str, qtd)
            proporcao = (qtd / total_periodo) if total_periodo > 0 else 0.0

            taxa_rec: float | None = None
            if coluna_voto is not None:
                taxa_rec = float(grupo[coluna_voto].astype(float).mean())

            media_horas: float | None = None
            if coluna_horas is not None:
                media_minutos = float(grupo[coluna_horas].astype(float).mean())
                media_horas = media_minutos / 60.0

            nome_rotulo = ROTULO_RUIDO if cid_int == -1 else f"Cluster {cid_int}"

            pontos_map[(periodo_str, cid_int)] = PontoTemporalCluster(
                periodo=periodo_str,
                id_cluster=cid_int,
                nome_rotulo=nome_rotulo,
                quantidade_amostras=qtd,
                proporcao_periodo=float(proporcao),
                taxa_recomendacao=taxa_rec,
                media_horas_jogadas=media_horas,
            )

        # Preenche períodos ausentes com 0 se solicitado
        if self._config.preencher_periodos_ausentes:
            for periodo in periodos_unicos:
                for cid in clusters_unicos:
                    chave = (periodo, cid)
                    if chave not in pontos_map:
                        nome_rotulo = ROTULO_RUIDO if cid == -1 else f"Cluster {cid}"
                        pontos_map[chave] = PontoTemporalCluster(
                            periodo=periodo,
                            id_cluster=cid,
                            nome_rotulo=nome_rotulo,
                            quantidade_amostras=0,
                            proporcao_periodo=0.0,
                            taxa_recomendacao=None,
                            media_horas_jogadas=None,
                        )

        # Ordena pontos por período cronológico e depois por ID do cluster
        pontos_ordenados = sorted(
            pontos_map.values(),
            key=lambda p: (p.periodo, p.id_cluster),
        )

        # Detecta anomalias estatísticas
        alertas = self._detector.detectar_picos(pontos_ordenados)

        return ResumoAnaliseTemporal(
            pontos_temporais=pontos_ordenados,
            periodos_ordenados=periodos_unicos,
            clusters_presentes=clusters_unicos,
            alertas_picos=alertas,
            granularidade=self._estrategia.obter_nome_granularidade(),
            coluna_temporal=coluna_tempo,
            total_amostras_temporais=len(df_validos),
        )
