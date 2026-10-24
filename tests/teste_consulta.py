"""Testes para o serviço analítico de recuperação de reviews brutas por cluster."""

import pandas as pd

from app.servico_consulta.recuperador_reviews import RecuperadorReviews


def teste_recuperacao_amostras_cluster() -> None:
    """Verifica a extração fiel de avaliações brutas originais para consulta humana."""
    dados = pd.DataFrame(
        {
            "recommendationid": ["r1", "r2", "r3", "r4", "r5"],
            "cluster_id": [0, 0, 1, 1, -1],
            "rotulo_negocio": ["veteranos", "veteranos", "novatos", "novatos", "ruido"],
            "review_texto": [
                "Jogo fantástico com mais de 500h de gameplay.",
                "Excelente mecânica e gráficos.",
                "Comecei agora e achei confuso.",
                "Muito bom para jogar com amigos.",
                "Travou no início.",
            ],
            "horas_jogadas_total": [520.0, 480.0, 5.0, 12.0, 0.5],
            "voted_up": [True, True, False, True, False],
            "votes_up": [15, 8, 2, 0, 1],
        }
    )

    recuperador = RecuperadorReviews()

    # 1. Recupera amostras de um cluster específico
    amostras_c0 = recuperador.recuperar_amostras_cluster(
        dados, cluster_id=0, quantidade=2
    )
    assert len(amostras_c0) == 2
    for a in amostras_c0:
        assert a.cluster_id == 0
        assert a.rotulo_negocio == "veteranos"
        assert len(a.review_texto) > 0

    # 2. Recupera mapa de todos os clusters
    mapa_geral = recuperador.recuperar_todas_por_cluster(
        dados, quantidade_por_cluster=5
    )
    assert set(mapa_geral.keys()) == {0, 1, -1}
    assert len(mapa_geral[0]) == 2
    assert len(mapa_geral[1]) == 2
    assert len(mapa_geral[-1]) == 1
    assert mapa_geral[-1][0].recommendationid == "r5"
