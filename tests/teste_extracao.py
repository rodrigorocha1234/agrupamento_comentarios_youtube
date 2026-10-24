"""Testes automatizados para cliente, adaptador e gerador paginado da Steam."""

from typing import final, override

from app.dominio_contratos.protocolos_extracao import ClienteSteam
from app.extracao_steam.controlador_resiliencia import ControladorResiliencia
from app.extracao_steam.gerador_paginas import GeradorPaginasSteam


@final
class ClienteSteamFalso(ClienteSteam):
    """Implementação mock do cliente da Steam para testes determinísticos."""

    def __init__(self, loop_proposital: bool = False) -> None:
        self.chamadas = 0
        self.loop_proposital = loop_proposital

    @override
    def buscar_pagina_bruta(
        self, appid: int, cursor: str, tamanho_pagina: int
    ) -> dict[str, object]:
        self.chamadas += 1

        if self.loop_proposital and self.chamadas >= 3:
            # Força repetição de cursor já visitado
            return {
                "cursor": "*",
                "reviews": [
                    {
                        "recommendationid": "999",
                        "author": {
                            "steamid": "1",
                            "num_games_owned": 10,
                            "num_reviews": 5,
                        },
                        "review": "Loop",
                        "timestamp_created": 100,
                        "timestamp_updated": 100,
                    }
                ],
            }

        if self.chamadas == 1:
            return {
                "cursor": "cursor_pagina_2",
                "reviews": [
                    {
                        "recommendationid": "1001",
                        "author": {
                            "steamid": "76561198000000001",
                            "num_games_owned": 150,
                            "num_reviews": 12,
                            "playtime_forever": 3600,
                            "playtime_last_two_weeks": 120,
                            "playtime_at_review": 1800,
                            "last_played": 1700000000,
                        },
                        "language": "brazilian",
                        "review": "Jogo excelente!",
                        "timestamp_created": 1690000000,
                        "timestamp_updated": 1690000000,
                        "voted_up": True,
                        "votes_up": 10,
                        "votes_funny": 2,
                        "weighted_vote_score": 0.85,
                        "comment_count": 1,
                        "steam_purchase": True,
                        "received_for_free": False,
                        "written_during_early_access": False,
                        "primarily_steam_deck": False,
                    }
                ],
            }
        elif self.chamadas == 2:
            return {
                "cursor": "cursor_pagina_3",
                "reviews": [
                    {
                        "recommendationid": "1002",
                        "author": {
                            "steamid": "76561198000000002",
                            "num_games_owned": 50,
                            "num_reviews": 3,
                            "playtime_forever": 600,
                            "playtime_last_two_weeks": 0,
                            "playtime_at_review": 600,
                            "last_played": 1680000000,
                        },
                        "language": "brazilian",
                        "review": "Bom jogo.",
                        "timestamp_created": 1680000000,
                        "timestamp_updated": 1680000000,
                        "voted_up": True,
                        "votes_up": 3,
                        "votes_funny": 0,
                        "weighted_vote_score": 0.60,
                        "comment_count": 0,
                        "steam_purchase": True,
                        "received_for_free": False,
                        "written_during_early_access": True,
                        "primarily_steam_deck": False,
                    }
                ],
            }
        else:
            # Esgotamento natural
            return {"cursor": None, "reviews": []}


def teste_gerador_paginas_fluxo_completo() -> None:
    """Verifica se o gerador lazy consome página a página e para na exaustão."""
    cliente_falso = ClienteSteamFalso()
    gerador = GeradorPaginasSteam(cliente=cliente_falso, maximo_paginas=10)

    paginas = list(gerador.iterar_paginas(appid=427520))

    assert len(paginas) == 2
    assert paginas[0].cursor_entrada == "*"
    assert paginas[0].cursor_proximo == "cursor_pagina_2"
    assert len(paginas[0].reviews) == 1
    assert paginas[0].reviews[0].recommendationid == "1001"
    assert paginas[0].reviews[0].review_texto == "Jogo excelente!"

    assert paginas[1].cursor_entrada == "cursor_pagina_2"
    assert paginas[1].reviews[0].recommendationid == "1002"
    assert cliente_falso.chamadas == 3


def teste_gerador_paginas_protecao_loop_cursor() -> None:
    """Garante que a repetição de um cursor já visitado encerra o gerador imediatamente."""
    cliente_loop = ClienteSteamFalso(loop_proposital=True)
    gerador = GeradorPaginasSteam(cliente=cliente_loop, maximo_paginas=10)

    paginas = list(gerador.iterar_paginas(appid=427520))

    # Deve encerrar ao detectar repetição sem loop infinito
    assert len(paginas) <= 3


def teste_controlador_resiliencia_backoff() -> None:
    """Valida o cálculo do backoff exponencial."""
    resiliencia = ControladorResiliencia(max_tentativas=3, espera_base_segundos=0.1)
    espera_1 = resiliencia.calcular_espera_backoff(1)
    espera_2 = resiliencia.calcular_espera_backoff(2)
    assert espera_2 > espera_1
