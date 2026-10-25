"""Módulo de extração e compatibilidade para a Steam Web API."""

from app.ingestao_fontes.adaptadores.adaptador_steam import (
    AdaptadorSteam as ClienteSteamAPI,
)
from app.ingestao_fontes.coletor_dados import ColetorDados as ColetorSteam

__all__ = ["ClienteSteamAPI", "ColetorSteam"]
