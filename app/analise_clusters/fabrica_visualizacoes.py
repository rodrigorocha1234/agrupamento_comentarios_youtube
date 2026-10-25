"""Fábrica (GoF Factory) para instanciação e registro de estratégias gráficas."""

from typing import ClassVar

from app.analise_clusters.estrategia_altair import EstrategiaVisualizacaoAltair
from app.analise_clusters.estrategia_plotly import EstrategiaVisualizacaoPlotly
from app.analise_clusters.estrategia_visualizacao import EstrategiaVisualizacao
from app.excecoes import ErroConfiguracao


class FabricaVisualizacoes:
    """Fábrica (GoF Factory) para instanciação e registro de estratégias gráficas."""

    _registro: ClassVar[dict[str, type[EstrategiaVisualizacao]]] = {
        "plotly": EstrategiaVisualizacaoPlotly,
        "altair": EstrategiaVisualizacaoAltair,
    }

    @classmethod
    def registrar_estrategia(
        cls,
        nome_engine: str,
        classe_estrategia: type[EstrategiaVisualizacao],
    ) -> None:
        """Permite plugar novas bibliotecas gráficas no runtime sem modificar código existente."""
        cls._registro[nome_engine.lower().strip()] = classe_estrategia

    @classmethod
    def criar_estrategia(cls, engine: str = "plotly") -> EstrategiaVisualizacao:
        """Instancia a estratégia correspondente à chave configurada no YAML."""
        chave = engine.lower().strip()
        classe = cls._registro.get(chave)
        if classe is None:
            suportadas = sorted(cls._registro.keys())
            raise ErroConfiguracao(
                f"Motor de visualização '{engine}' não suportado. Motores registrados: {suportadas}"
            )
        return classe()
