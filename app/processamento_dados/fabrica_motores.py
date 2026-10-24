"""Fábrica e Registry de motores tabulares sem seleção por if/elif no domínio."""

from collections.abc import Callable
from typing import Final, final

from app.processamento_dados.motor_pandas import MotorPandas
from app.processamento_dados.motor_polars import MotorPolars

TipoCriadorMotor = Callable[[], MotorPandas | MotorPolars]


class ErroMotorTabularNaoRegistrado(Exception):
    """Exceção levantada quando um motor solicitado não estiver no catálogo de registros."""


@final
class FabricaMotores:
    """Registry e Factory para instanciar motores tabulares (Pandas / Polars)."""

    def __init__(self) -> None:
        self._registro: Final[dict[str, TipoCriadorMotor]] = {}
        self._registrar_padroes()

    def registrar_motor(self, nome: str, criador: TipoCriadorMotor) -> None:
        """Registra um novo motor tabular."""
        self._registro[nome.lower()] = criador

    def criar_motor(self, nome: str) -> MotorPandas | MotorPolars:
        """Resolve o motor registrado sem condicionais if/elif no domínio."""
        chave = nome.lower()
        criador = self._registro.get(chave)
        if criador is None:
            raise ErroMotorTabularNaoRegistrado(
                f"Motor tabular '{nome}' não suportado. Opções registradas: {list(self._registro.keys())}"
            )
        return criador()

    def _registrar_padroes(self) -> None:
        """Registra os motores oficiais do projeto."""
        self.registrar_motor("pandas", lambda: MotorPandas())
        self.registrar_motor("polars", lambda: MotorPolars())
