"""Detector estatístico de anomalias cronológicas e picos incomuns de avaliações."""

import numpy as np

from app.analise_temporal.contratos import AlertaPicoTemporal, PontoTemporalCluster
from app.conf_yaml import ConfigDeteccaoPicosInfo


class DetectorAnomaliasTemporais:
    """Calcula Z-scores e desvios estatísticos para detectar eventos anômalos por cluster."""

    def __init__(self, config: ConfigDeteccaoPicosInfo | None = None) -> None:
        self._config = config or ConfigDeteccaoPicosInfo()

    def detectar_picos(self, pontos: list[PontoTemporalCluster]) -> list[AlertaPicoTemporal]:
        """Identifica períodos em que o volume ou composição do cluster desviou da distribuição histórica."""
        if not self._config.habilitado or not pontos:
            return []

        alertas: list[AlertaPicoTemporal] = []
        clusters = sorted({p.id_cluster for p in pontos})

        for cid in clusters:
            pontos_cluster = [p for p in pontos if p.id_cluster == cid]
            if len(pontos_cluster) < 3:
                # Períodos insuficientes para calcular dispersão histórica confiável
                continue

            volumes = np.array([p.quantidade_amostras for p in pontos_cluster], dtype=float)
            media_vol = float(np.mean(volumes))
            desvio_vol = float(np.std(volumes))

            if desvio_vol <= 1e-6:
                continue

            for ponto in pontos_cluster:
                if ponto.quantidade_amostras < self._config.minimo_amostras_periodo:
                    continue

                z_score = (ponto.quantidade_amostras - media_vol) / desvio_vol
                if z_score >= self._config.limiar_desvio_padrao:
                    descricao = (
                        f"Pico de avaliações no período {ponto.periodo} para o {ponto.nome_rotulo}: "
                        f"{ponto.quantidade_amostras} avaliações (Média: {media_vol:.1f}, "
                        f"Desvio Z: +{z_score:.2f}σ)."
                    )
                    alertas.append(
                        AlertaPicoTemporal(
                            periodo=ponto.periodo,
                            id_cluster=ponto.id_cluster,
                            nome_rotulo=ponto.nome_rotulo,
                            tipo_alerta="pico_volume",
                            z_score=float(z_score),
                            valor_observado=float(ponto.quantidade_amostras),
                            media_historica=media_vol,
                            descricao=descricao,
                        )
                    )

        return alertas
