"""Fábrica (GoF Factory Method) para instanciação do analisador temporal."""

from app.analise_temporal.analisador_temporal import AnalisadorTemporalClusters
from app.analise_temporal.detector_anomalias import DetectorAnomaliasTemporais
from app.analise_temporal.estrategia_agregacao import (
    AgregadorAnual,
    AgregadorDiario,
    AgregadorMensal,
    AgregadorSemanal,
    EstrategiaAgregacaoTemporal,
)
from app.conf_yaml import ConfigAnaliseTemporalInfo


class FabricaAnaliseTemporal:
    """Instancia os componentes de análise temporal a partir das especificações do YAML."""

    @classmethod
    def criar_estrategia(cls, granularidade: str) -> EstrategiaAgregacaoTemporal:
        """Fabrica a estratégia de discretização temporal com base no identificador textual."""
        estrategias: dict[str, type[EstrategiaAgregacaoTemporal]] = {
            "mensal": AgregadorMensal,
            "semanal": AgregadorSemanal,
            "diaria": AgregadorDiario,
            "anual": AgregadorAnual,
        }
        classe_estrategia = estrategias.get(granularidade.lower(), AgregadorMensal)
        return classe_estrategia()

    @classmethod
    def criar_analisador(
        cls,
        config: ConfigAnaliseTemporalInfo | None = None,
    ) -> AnalisadorTemporalClusters:
        """Instancia e conecta a estratégia, detector e analisador temporal."""
        cfg = config or ConfigAnaliseTemporalInfo()
        estrategia = cls.criar_estrategia(cfg.granularidade)
        detector = DetectorAnomaliasTemporais(cfg.deteccao_picos)
        return AnalisadorTemporalClusters(
            estrategia=estrategia,
            detector=detector,
            config=cfg,
        )
