"""Testes automatizados para o Quality Gate de validação de dados."""

from app.dominio_contratos.modelos_dados import AutorSteam, ReviewSteam
from app.observabilidade_metricas.validador_qualidade import ValidadorQualidadeDados


def teste_quality_gate_lote_valido() -> None:
    """Verifica aprovação de um lote íntegro."""
    validador = ValidadorQualidadeDados()
    autor = AutorSteam(
        steamid="1",
        num_games_owned=10,
        num_reviews=5,
        playtime_forever=100,
        playtime_last_two_weeks=10,
        playtime_at_review=50,
        last_played=1700000000,
    )
    review = ReviewSteam(
        appid=427520,
        recommendationid="REC_1",
        author=autor,
        language="brazilian",
        review_texto="Tudo certo",
        timestamp_created=1690000000,
        timestamp_updated=1690000000,
        voted_up=True,
        votes_up=0,
        votes_funny=0,
        weighted_vote_score=0.0,
        comment_count=0,
        steam_purchase=True,
        received_for_free=False,
        written_during_early_access=False,
        primarily_steam_deck=False,
    )

    relatorio = validador.validar_lote_reviews([review])
    assert relatorio.aprovado is True
    assert relatorio.total_duplicados == 0
    assert len(relatorio.mensagens_bloqueantes) == 0


def teste_quality_gate_rejeita_duplicatas() -> None:
    """Garante rejeição quando houver colisão de (appid, recommendationid)."""
    validador = ValidadorQualidadeDados()
    autor = AutorSteam(
        steamid="1",
        num_games_owned=10,
        num_reviews=5,
        playtime_forever=100,
        playtime_last_two_weeks=10,
        playtime_at_review=50,
        last_played=1700000000,
    )
    review = ReviewSteam(
        appid=427520,
        recommendationid="REC_1",
        author=autor,
        language="brazilian",
        review_texto="Teste",
        timestamp_created=1690000000,
        timestamp_updated=1690000000,
        voted_up=True,
        votes_up=0,
        votes_funny=0,
        weighted_vote_score=0.0,
        comment_count=0,
        steam_purchase=True,
        received_for_free=False,
        written_during_early_access=False,
        primarily_steam_deck=False,
    )

    relatorio = validador.validar_lote_reviews([review, review])
    assert relatorio.aprovado is False
    assert relatorio.total_duplicados == 1
    assert any("duplicatas" in msg for msg in relatorio.mensagens_bloqueantes)


def teste_quality_gate_rejeita_tempos_negativos() -> None:
    """Garante rejeição para domínios numéricos inconsistentes."""
    validador = ValidadorQualidadeDados()
    autor_invalido = AutorSteam(
        steamid="1",
        num_games_owned=10,
        num_reviews=5,
        playtime_forever=-50,
        playtime_last_two_weeks=0,
        playtime_at_review=0,
        last_played=1700000000,
    )
    review = ReviewSteam(
        appid=427520,
        recommendationid="REC_2",
        author=autor_invalido,
        language="brazilian",
        review_texto="Tempo negativo",
        timestamp_created=1690000000,
        timestamp_updated=1690000000,
        voted_up=True,
        votes_up=0,
        votes_funny=0,
        weighted_vote_score=0.0,
        comment_count=0,
        steam_purchase=True,
        received_for_free=False,
        written_during_early_access=False,
        primarily_steam_deck=False,
    )

    relatorio = validador.validar_lote_reviews([review])
    assert relatorio.aprovado is False
    assert relatorio.total_valores_invalidos == 1
    assert any(
        "tempos de jogo negativos" in msg for msg in relatorio.mensagens_bloqueantes
    )
