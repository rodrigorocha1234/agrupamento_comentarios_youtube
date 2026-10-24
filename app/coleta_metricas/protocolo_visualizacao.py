"""Protocolo estrutural para provedores de dashboards e visualização operacional."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.configuracao_geral.tipos_enumerados import TipoProvedorVisualizacao


@runtime_checkable
class ProtocoloProvedorVisualizacao(Protocol):
    """Contrato abstrato que qualquer provedor de visualização (Grafana, Kibana, etc.) deve implementar."""

    @property
    def tipo_provedor(self) -> TipoProvedorVisualizacao:
        """Identificador canônico do tipo de provedor."""
        ...

    @property
    def url_base(self) -> str:
        """URL base de conexão com o servidor de visualização."""
        ...

    def verificar_disponibilidade(self, timeout_segundos: float = 2.0) -> bool:
        """Verifica se o serviço de visualização está ativo e acessível."""
        ...

    def obter_url_dashboard(self, identificador: str) -> str:
        """Retorna a URL absoluta navegável para um dashboard específico."""
        ...

    def listar_dashboards(self) -> list[dict[str, Any]]:
        """Lista os dashboards e painéis disponibilizados pelo provedor."""
        ...

    def obter_metadados_painel(self, identificador: str) -> dict[str, Any]:
        """Obtém detalhes descritivos e metadados de um painel/dashboard."""
        ...
