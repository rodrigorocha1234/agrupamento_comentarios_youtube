"""Estratégias de análise pós-agrupamento para problemas temporais e estáticos.

Aplica os padrões Strategy e Factory para separar o tratamento analítico
de séries temporais (tendências, deltas e janelas) de problemas estáticos
cross-sectional (distribuição pura, perfil de clusters sem tempo).
"""

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar, runtime_checkable

from app.analise_tendencias.detector_variacao import DetectorVariacao, ResultadoVariacao
from app.configuracao_geral.modelos_configuracao import (
    ConfiguracaoGlobal,
    ConfiguracaoProcessamento,
    ConfiguracaoTendencias,
)
from app.configuracao_geral.tipos_enumerados import StatusTendencia

TIdentificador = TypeVar("TIdentificador", bound=str)


@dataclass(frozen=True, slots=True)
class ResultadoAnaliseCluster(Generic[TIdentificador]):
    """Consolida a análise de um cluster ou tópico sob uma estratégia analítica."""

    identificador: TIdentificador
    contagem: int
    proporcao: float
    status: StatusTendencia
    variacao_proporcao: float = 0.0
    percentual_variacao: float = 0.0


@runtime_checkable
class EstrategiaAnaliseClusters(Protocol[TIdentificador]):
    """Contrato (Strategy) para análise comportamental de clusters e tópicos."""

    def eh_temporal(self) -> bool:
        """Indica se a estratégia atua sobre dimensão temporal."""
        ...

    def classificar_grupo(
        self,
        contagem_atual: int,
        contagem_anterior: int = 0,
    ) -> ResultadoVariacao:
        """Determina o status de variação de um grupo individual."""
        ...

    def analisar_grupos(
        self,
        contagens_atuais: dict[TIdentificador, int],
        contagens_anteriores: dict[TIdentificador, int] | None = None,
    ) -> list[ResultadoAnaliseCluster[TIdentificador]]:
        """Consolida a distribuição e o comportamento de múltiplos grupos."""
        ...



class EstrategiaAnaliseTemporal:
    """Estratégia concreta para problemas temporais baseada em janelas e deltas."""

    def __init__(
        self,
        minimo_comentarios: int = 5,
        crescimento_minimo_proporcao: float = 0.10,
        queda_minima_proporcao: float = 0.10,
    ) -> None:
        self._detector = DetectorVariacao(
            minimo_comentarios=minimo_comentarios,
            crescimento_minimo_proporcao=crescimento_minimo_proporcao,
            queda_minima_proporcao=queda_minima_proporcao,
        )

    def eh_temporal(self) -> bool:
        return True

    def classificar_grupo(
        self,
        contagem_atual: int,
        contagem_anterior: int = 0,
    ) -> ResultadoVariacao:
        return self._detector.classificar(
            contagem_atual=contagem_atual,
            contagem_anterior=contagem_anterior,
        )

    def analisar_grupos(
        self,
        contagens_atuais: dict[str, int],
        contagens_anteriores: dict[str, int] | None = None,
    ) -> list[ResultadoAnaliseCluster[str]]:
        anteriores = contagens_anteriores or {}
        total = sum(contagens_atuais.values())
        resultados: list[ResultadoAnaliseCluster[str]] = []

        todos_chaves = sorted(set(contagens_atuais.keys()) | set(anteriores.keys()))
        for chave in todos_chaves:
            c_atual = contagens_atuais.get(chave, 0)
            c_anterior = anteriores.get(chave, 0)
            if c_atual == 0 and c_anterior == 0:
                continue

            var = self._detector.classificar(c_atual, c_anterior)
            status_enum = (
                var.status_tendencia
                if isinstance(var.status_tendencia, StatusTendencia)
                else StatusTendencia(str(var.status_tendencia))
            )
            prop = round(c_atual / total, 4) if total > 0 else 0.0

            resultados.append(
                ResultadoAnaliseCluster(
                    identificador=chave,
                    contagem=c_atual,
                    proporcao=prop,
                    status=status_enum,
                    variacao_proporcao=var.variacao_proporcao,
                    percentual_variacao=var.percentual_variacao,
                )
            )

        return resultados


class EstrategiaAnaliseEstatica:
    """Estratégia concreta para problemas estáticos / cross-sectional (sem tempo)."""

    def __init__(self, minimo_amostras: int = 1) -> None:
        self._minimo_amostras = max(1, minimo_amostras)

    def eh_temporal(self) -> bool:
        return False

    def classificar_grupo(
        self,
        contagem_atual: int,
        contagem_anterior: int = 0,
    ) -> ResultadoVariacao:
        status = (
            StatusTendencia.ESTATICO
            if contagem_atual >= self._minimo_amostras
            else StatusTendencia.SEM_DADOS
        )
        return ResultadoVariacao(
            contagem_atual=contagem_atual,
            contagem_anterior=0,
            variacao_proporcao=0.0,
            status_tendencia=status,
            percentual_variacao=0.0,
        )

    def analisar_grupos(
        self,
        contagens_atuais: dict[str, int],
        contagens_anteriores: dict[str, int] | None = None,
    ) -> list[ResultadoAnaliseCluster[str]]:
        total = sum(contagens_atuais.values())
        resultados: list[ResultadoAnaliseCluster[str]] = []

        for chave in sorted(contagens_atuais.keys()):
            c_atual = contagens_atuais[chave]
            prop = round(c_atual / total, 4) if total > 0 else 0.0
            status = (
                StatusTendencia.ESTATICO
                if c_atual >= self._minimo_amostras
                else StatusTendencia.SEM_DADOS
            )

            resultados.append(
                ResultadoAnaliseCluster(
                    identificador=chave,
                    contagem=c_atual,
                    proporcao=prop,
                    status=status,
                    variacao_proporcao=0.0,
                    percentual_variacao=0.0,
                )
            )

        return resultados


class FabricaEstrategiaAnalise:
    """Fábrica (Factory Pattern) para instanciar a estratégia analítica adequada."""

    @classmethod
    def criar_estrategia(
        cls,
        config: ConfiguracaoGlobal | ConfiguracaoProcessamento | ConfiguracaoTendencias | bool,
        minimo_comentarios: int = 5,
        crescimento_minimo_proporcao: float = 0.10,
        queda_minima_proporcao: float = 0.10,
    ) -> EstrategiaAnaliseClusters[str]:
        """Instancia a estratégia apropriada com base na flag eh_temporal/ativa."""
        eh_temporal = True

        if isinstance(config, bool):
            eh_temporal = config
        elif isinstance(config, ConfiguracaoGlobal):
            eh_temporal = config.processamento.eh_temporal and config.tendencias.ativa
            minimo_comentarios = config.tendencias.minimo_comentarios
            crescimento_minimo_proporcao = config.tendencias.crescimento_minimo_proporcao
            queda_minima_proporcao = config.tendencias.queda_minima_proporcao
        elif isinstance(config, ConfiguracaoProcessamento):
            eh_temporal = config.eh_temporal
        else:
            eh_temporal = config.ativa
            minimo_comentarios = config.minimo_comentarios
            crescimento_minimo_proporcao = config.crescimento_minimo_proporcao
            queda_minima_proporcao = config.queda_minima_proporcao

        if eh_temporal:
            return EstrategiaAnaliseTemporal(
                minimo_comentarios=minimo_comentarios,
                crescimento_minimo_proporcao=crescimento_minimo_proporcao,
                queda_minima_proporcao=queda_minima_proporcao,
            )

        return EstrategiaAnaliseEstatica(minimo_amostras=minimo_comentarios)
