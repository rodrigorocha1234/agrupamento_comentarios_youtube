from dataclasses import dataclass
from typing import final

from app.avaliacao_modelos.metricas_estatisticas import ResultadoAvaliacao


@dataclass(frozen=True, slots=True)
class ResultadoObjetivo:
    """Resultado do cálculo multicritério de qualidade de agrupamento."""

    score_composto: float
    valido: bool
    justificativa: str


@final
class AvaliadorObjetivo:
    """Calcula pontuação composta equilibrando coesão, separabilidade e taxa de ruído."""

    def calcular_score(self, metricas: ResultadoAvaliacao) -> ResultadoObjetivo:
        """Avalia as métricas segundo múltiplos critérios sem se basear em uma única métrica."""
        # Se cluster único ou todo o conjunto for ruído, resultado inválido
        if metricas.total_clusters <= 1:
            return ResultadoObjetivo(
                score_composto=-1.0,
                valido=False,
                justificativa="Modelo com menos de 2 clusters válidos.",
            )

        # Se proporção de ruído for excessiva (> 80%)
        if metricas.proporcao_ruido > 0.8:
            return ResultadoObjetivo(
                score_composto=-0.5,
                valido=False,
                justificativa=f"Taxa de ruído excessiva: {metricas.proporcao_ruido:.1%}.",
            )

        # Silhueta sem ruído como base (se disponível, senão silhueta global)
        sil = metricas.silhouette_sem_ruido
        if sil is None or sil <= -1.0:
            sil = metricas.silhouette_global or -1.0

        # Fator de penalização por ruído
        fator_aproveitamento = 1.0 - metricas.proporcao_ruido

        # Davies-Bouldin: quanto menor melhor (0 é ideal). Penaliza se DB > 1.5
        db_penalidade = 0.0
        if metricas.davies_bouldin is not None and metricas.davies_bouldin > 1.5:
            db_penalidade = min(0.3, (metricas.davies_bouldin - 1.5) * 0.1)

        score_final = (sil * fator_aproveitamento) - db_penalidade

        return ResultadoObjetivo(
            score_composto=float(score_final),
            valido=True,
            justificativa="Pontuação balanceada entre silhueta, ruído e separabilidade.",
        )
