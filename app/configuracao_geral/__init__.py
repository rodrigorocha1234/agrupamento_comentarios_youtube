"""Pacote de carregamento e tipagem de configurações gerais do sistema."""

from app.configuracao_geral.modelos_configuracao import ConfiguracaoGlobal
from app.configuracao_geral.provedor_configuracao import ProvedorConfiguracao
from app.configuracao_geral.tipos_enumerados import (
    CamadaLakehouse,
    JanelaTemporal,
    OrigemComentario,
    PeriodicidadeColeta,
    StatusSaude,
    StatusTendencia,
    TecnicaCluster,
    TecnicaReducao,
    TecnicaRepresentacao,
)

__all__ = [
    "CamadaLakehouse",
    "ConfiguracaoGlobal",
    "JanelaTemporal",
    "OrigemComentario",
    "PeriodicidadeColeta",
    "ProvedorConfiguracao",
    "StatusSaude",
    "StatusTendencia",
    "TecnicaCluster",
    "TecnicaReducao",
    "TecnicaRepresentacao",
]
