"""Contratos para observabilidade analítica e rastreamento de experimentos com MLflow."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProtocoloObservadorExperimento(Protocol):
    """Protocolo abstrato (Observer) para rastreamento de parâmetros, métricas e artefatos."""

    def registrar_parametros(self, parametros: dict[str, str | int | float | bool]) -> None:
        """Registra parâmetros do experimento."""
        ...

    def registrar_metricas(self, metricas: dict[str, float]) -> None:
        """Registra métricas escalares do experimento."""
        ...

    def registrar_tags(self, tags: dict[str, str]) -> None:
        """Registra metadados e tags contextuais do experimento."""
        ...

    def registrar_artefato(self, caminho_local: str, subpasta_destino: str | None = None) -> None:
        """Registra arquivo de artefato (ex.: gráficos HTML, perfis) no servidor de tracking."""
        ...
