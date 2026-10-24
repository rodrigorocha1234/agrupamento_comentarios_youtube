"""Implementação nula (Null Object Pattern) do provedor de visualização."""

from __future__ import annotations

from typing import Any

from app.coleta_metricas.protocolo_visualizacao import ProtocoloProvedorVisualizacao
from app.configuracao_geral.tipos_enumerados import TipoProvedorVisualizacao


class ProvedorVisualizacaoNulo(ProtocoloProvedorVisualizacao):
    """Provedor nulo utilizado quando a visualização está desativada ou não configurada."""

    def __init__(self, url_base: str = "") -> None:
        self._url_base = url_base

    @property
    def tipo_provedor(self) -> TipoProvedorVisualizacao:
        return TipoProvedorVisualizacao.NENHUM

    @property
    def url_base(self) -> str:
        return self._url_base

    def verificar_disponibilidade(self, timeout_segundos: float = 2.0) -> bool:
        return False

    def obter_url_dashboard(self, identificador: str) -> str:
        return ""

    def listar_dashboards(self) -> list[dict[str, Any]]:
        return []

    def obter_metadados_painel(self, identificador: str) -> dict[str, Any]:
        return {
            "uid": identificador,
            "url": "",
            "status": "desativado",
        }
