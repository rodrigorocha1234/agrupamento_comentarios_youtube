"""Classificador determinístico da variação temporal de tópicos."""

from dataclasses import dataclass

from app.configuracao_geral.tipos_enumerados import StatusTendencia


@dataclass(frozen=True, slots=True)
class ResultadoVariacao:
    """Consolida os cálculos de variação e classificação de tendência de um tópico."""

    contagem_atual: int
    contagem_anterior: int
    variacao_proporcao: float
    status_tendencia: StatusTendencia | str
    percentual_variacao: float = 0.0


class DetectorVariacao:
    """Calcula a taxa de crescimento e classifica o status da tendência de forma auditável."""

    def __init__(
        self,
        minimo_comentarios: int = 5,
        crescimento_minimo_proporcao: float = 0.10,
        queda_minima_proporcao: float = 0.10,
    ) -> None:
        self._minimo_comentarios: int = max(1, minimo_comentarios)
        self._crescimento_limiar: float = abs(crescimento_minimo_proporcao)
        self._queda_limiar: float = abs(queda_minima_proporcao)

    def classificar(
        self,
        contagem_atual: int,
        contagem_anterior: int,
    ) -> ResultadoVariacao:
        """Determina o status da tendência tratando explicitamente divisões por zero e suporte mínimo."""
        total = contagem_atual + contagem_anterior
        if total < self._minimo_comentarios:
            return ResultadoVariacao(
                contagem_atual=contagem_atual,
                contagem_anterior=contagem_anterior,
                variacao_proporcao=0.0,
                status_tendencia=StatusTendencia.SEM_DADOS,
                percentual_variacao=0.0,
            )

        if contagem_anterior == 0:
            return ResultadoVariacao(
                contagem_atual=contagem_atual,
                contagem_anterior=0,
                variacao_proporcao=1.0,
                status_tendencia=StatusTendencia.NOVO,
                percentual_variacao=100.0,
            )

        variacao = (contagem_atual - contagem_anterior) / float(contagem_anterior)
        percentual = round(variacao * 100.0, 2)

        if variacao > self._crescimento_limiar:
            status = StatusTendencia.CRESCENDO
        elif variacao < -self._queda_limiar:
            status = StatusTendencia.DECRESCENDO
        else:
            status = StatusTendencia.ESTAVEL

        return ResultadoVariacao(
            contagem_atual=contagem_atual,
            contagem_anterior=contagem_anterior,
            variacao_proporcao=float(variacao),
            status_tendencia=status,
            percentual_variacao=percentual,
        )
