"""Estratégias GoF (Strategy) para resolução e agregação de granularidades temporais."""

from abc import ABC, abstractmethod

import pandas as pd


class EstrategiaAgregacaoTemporal(ABC):
    """Contrato base GoF Strategy para discretização de séries cronológicas."""

    @abstractmethod
    def normalizar_periodos(self, serie_timestamps: pd.Series) -> pd.Series:
        """Converte Unix timestamps em strings de períodos canônicos e ordenáveis."""

    @abstractmethod
    def obter_nome_granularidade(self) -> str:
        """Retorna o identificador textual da granularidade."""


class AgregadorMensal(EstrategiaAgregacaoTemporal):
    """Agrega eventos na escala de Ano-Mês (ex: 2024-03)."""

    def normalizar_periodos(self, serie_timestamps: pd.Series) -> pd.Series:
        datas = pd.to_datetime(serie_timestamps, unit="s", errors="coerce")
        return datas.dt.strftime("%Y-%m").fillna("Desconhecido")

    def obter_nome_granularidade(self) -> str:
        return "mensal"


class AgregadorSemanal(EstrategiaAgregacaoTemporal):
    """Agrega eventos na escala de Ano-Semana (ex: 2024-W12)."""

    def normalizar_periodos(self, serie_timestamps: pd.Series) -> pd.Series:
        datas = pd.to_datetime(serie_timestamps, unit="s", errors="coerce")
        return datas.dt.strftime("%Y-W%U").fillna("Desconhecido")

    def obter_nome_granularidade(self) -> str:
        return "semanal"


class AgregadorDiario(EstrategiaAgregacaoTemporal):
    """Agrega eventos na escala diária (ex: 2024-03-15)."""

    def normalizar_periodos(self, serie_timestamps: pd.Series) -> pd.Series:
        datas = pd.to_datetime(serie_timestamps, unit="s", errors="coerce")
        return datas.dt.strftime("%Y-%m-%d").fillna("Desconhecido")

    def obter_nome_granularidade(self) -> str:
        return "diaria"


class AgregadorAnual(EstrategiaAgregacaoTemporal):
    """Agrega eventos na escala anual (ex: 2024)."""

    def normalizar_periodos(self, serie_timestamps: pd.Series) -> pd.Series:
        datas = pd.to_datetime(serie_timestamps, unit="s", errors="coerce")
        return datas.dt.strftime("%Y").fillna("Desconhecido")

    def obter_nome_granularidade(self) -> str:
        return "anual"
