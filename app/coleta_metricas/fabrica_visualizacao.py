"""Fábrica polimórfica para criação e instanciação de provedores de visualização."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from app.coleta_metricas.protocolo_visualizacao import ProtocoloProvedorVisualizacao
from app.coleta_metricas.provedor_grafana import ProvedorVisualizacaoGrafana
from app.coleta_metricas.provedor_nulo import ProvedorVisualizacaoNulo
from app.configuracao_geral.modelos_configuracao import ConfiguracaoObservabilidade
from app.configuracao_geral.tipos_enumerados import TipoProvedorVisualizacao

if TYPE_CHECKING:
    from app.configuracao_geral.modelos_configuracao import ConfiguracaoGlobal


class FabricaProvedorVisualizacao:
    """Fábrica que resolve o provedor de dashboards/visualização conforme a configuração."""

    _registro_provedores: dict[
        TipoProvedorVisualizacao, Callable[[str], ProtocoloProvedorVisualizacao]
    ] = {
        TipoProvedorVisualizacao.GRAFANA: lambda url: ProvedorVisualizacaoGrafana(url_base=url),
        TipoProvedorVisualizacao.NENHUM: lambda url: ProvedorVisualizacaoNulo(url_base=url),
    }

    @classmethod
    def registrar_provedor(
        cls,
        tipo: TipoProvedorVisualizacao,
        fabrica: Callable[[str], ProtocoloProvedorVisualizacao],
    ) -> None:
        """Permite plugar e estender dinamicamente novos provedores de visualização (ex: Kibana, Datadog)."""
        cls._registro_provedores[tipo] = fabrica

    @classmethod
    def criar_provedor(
        cls, config: ConfiguracaoGlobal | ConfiguracaoObservabilidade
    ) -> ProtocoloProvedorVisualizacao:
        """Instancia o provedor de visualização configurado."""
        if isinstance(config, ConfiguracaoObservabilidade):
            obs = config
        else:
            obs = config.observabilidade

        if not obs.grafana and obs.provedor_visualizacao == TipoProvedorVisualizacao.GRAFANA:
            return ProvedorVisualizacaoNulo(url_base=obs.url_visualizacao)

        construtor = cls._registro_provedores.get(obs.provedor_visualizacao)
        if construtor is not None:
            return construtor(obs.url_visualizacao)

        return ProvedorVisualizacaoNulo(url_base=obs.url_visualizacao)
