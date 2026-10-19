"""Testes unitários rigorosos para a fase de detecção e agregação de tendências."""

from datetime import datetime, timedelta, timezone

from app.analise_tendencias.agregador_visoes import AgregadorVisoes
from app.analise_tendencias.calculador_tendencias import CalculadorTendencias
from app.analise_tendencias.detector_variacao import DetectorVariacao
from app.coleta_youtube.modelos_coleta import ComentarioColetado
from app.gestao_dados.camada_ouro import RegistroTopicoOuro


def test_detector_variacao_classificacoes() -> None:
    """Verifica todos os estados de transição de tendências e proteção contra divisão por zero."""
    detector = DetectorVariacao(
        minimo_comentarios=5,
        crescimento_minimo_proporcao=0.10,
        queda_minima_proporcao=0.10,
    )

    # 1. Sem dados suficientes (< 5)
    r1 = detector.classificar(contagem_atual=2, contagem_anterior=1)
    assert r1.status_tendencia == "sem_dados"
    assert r1.percentual_variacao == 0.0

    # 2. Tópico novo (anterior 0, atual >= 5)
    r2 = detector.classificar(contagem_atual=10, contagem_anterior=0)
    assert r2.status_tendencia == "novo"
    assert r2.variacao_proporcao == 1.0
    assert r2.percentual_variacao == 100.0

    # 3. Crescendo (+100%)
    r3 = detector.classificar(contagem_atual=20, contagem_anterior=10)
    assert r3.status_tendencia == "crescendo"
    assert r3.variacao_proporcao == 1.0
    assert r3.percentual_variacao == 100.0

    # 4. Decrescendo (-50%)
    r4 = detector.classificar(contagem_atual=5, contagem_anterior=10)
    assert r4.status_tendencia == "decrescendo"
    assert r4.variacao_proporcao == -0.5
    assert r4.percentual_variacao == -50.0

    # 5. Estável (+5%)
    r5 = detector.classificar(contagem_atual=21, contagem_anterior=20)
    assert r5.status_tendencia == "estavel"
    assert r5.percentual_variacao == 5.0


def test_calculador_tendencias_e_amostras() -> None:
    """Testa segregação de comentários em janelas temporais contíguas de 7 dias."""
    detector = DetectorVariacao(minimo_comentarios=3)
    calculador = CalculadorTendencias(janela_dias=7, detector=detector)

    referencia = datetime(2026, 10, 15, 12, 0, 0, tzinfo=timezone.utc)
    data_atual = referencia - timedelta(days=2)
    data_anterior = referencia - timedelta(days=9)

    comentarios: list[ComentarioColetado] = []
    # 4 comentários na janela atual para o tópico 'python'
    for i in range(4):
        comentarios.append(
            ComentarioColetado(
                id_comentario=f"C_ATUAL_{i}",
                id_video="V1",
                id_canal="UC1",
                id_comentario_pai=None,
                etag="etag",
                texto_original=f"Python teste {i}",
                hash_conteudo=f"hash_{i}",
                publicado_em=data_atual,
                atualizado_em=data_atual,
                contagem_curtidas=1,
                origem="principal",
                coletado_em=referencia,
            )
        )
    # 1 comentário na janela anterior para o tópico 'python'
    comentarios.append(
        ComentarioColetado(
            id_comentario="C_ANT_0",
            id_video="V1",
            id_canal="UC1",
            id_comentario_pai=None,
            etag="etag",
            texto_original="Python antigo",
            hash_conteudo="hash_ant",
            publicado_em=data_anterior,
            atualizado_em=data_anterior,
            contagem_curtidas=1,
            origem="principal",
            coletado_em=referencia,
        )
    )

    topicos_map = {c.id_comentario: "python" for c in comentarios}
    registros = calculador.calcular_tendencias_video(
        id_canal="UC1",
        id_video="V1",
        tecnica="kmeans",
        topicos_por_comentario=topicos_map,
        comentarios=comentarios,
        referencia_temporal=referencia,
    )

    assert len(registros) == 1
    reg = registros[0]
    assert reg.topico == "python"
    assert reg.contagem_atual == 4
    assert reg.contagem_anterior == 1
    assert reg.status_tendencia == "crescendo"
    assert reg.data_referencia == "2026-10-15"
    assert reg.percentual_variacao == 300.0
    assert "Python teste 0" in reg.comentarios_amostra


def test_agregador_visoes_consolida_videos_do_canal() -> None:
    """Verifica consolidação de múltiplos vídeos de um canal em um registro único."""
    agregador = AgregadorVisoes()
    reg_v1 = RegistroTopicoOuro(
        id_canal="UC1",
        id_video="V1",
        tecnica="dbscan",
        topico="ia",
        contagem_atual=10,
        contagem_anterior=5,
        variacao_proporcao=1.0,
        status_tendencia="crescendo",
        comentarios_amostra="C1,C2",
        janela="7dias",
        data_referencia="2026-10-14",
        percentual_variacao=100.0,
    )
    reg_v2 = RegistroTopicoOuro(
        id_canal="UC1",
        id_video="V2",
        tecnica="dbscan",
        topico="ia",
        contagem_atual=15,
        contagem_anterior=5,
        variacao_proporcao=2.0,
        status_tendencia="crescendo",
        comentarios_amostra="C3,C4",
        janela="7dias",
        data_referencia="2026-10-14",
        percentual_variacao=200.0,
    )

    consolidados = agregador.consolidar_canal(
        id_canal="UC1",
        tecnica="dbscan",
        janela="7dias",
        topicos_dos_videos=[reg_v1, reg_v2],
    )

    assert len(consolidados) == 1
    c = consolidados[0]
    assert c.id_canal == "UC1"
    assert c.id_video == "consolidado"
    assert c.topico == "ia"
    assert c.contagem_atual == 25
    assert c.contagem_anterior == 10
    assert c.status_tendencia == "crescendo"
    assert c.data_referencia == "2026-10-14"
    assert c.percentual_variacao == 150.0
    assert "C1" in c.comentarios_amostra
    assert "C3" in c.comentarios_amostra


def test_segregacao_diaria_trends() -> None:
    """Verifica criação de trends segregadas por dia (hoje vs amanha) com percentuais de variacao."""
    detector = DetectorVariacao(minimo_comentarios=2)
    calculador = CalculadorTendencias(janela_dias=1, detector=detector)

    hoje = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)
    amanha = hoje + timedelta(days=1)

    # Dia 1 (Hoje): Tópico 'ia' novo
    c_hoje = [
        ComentarioColetado(
            id_comentario=f"CH_{i}",
            id_video="V1",
            id_canal="UC1",
            id_comentario_pai=None,
            etag="e",
            texto_original=f"Hoje comentário {i}",
            hash_conteudo=f"h_{i}",
            publicado_em=hoje - timedelta(hours=2),
            atualizado_em=hoje - timedelta(hours=2),
            contagem_curtidas=1,
            origem="principal",
            coletado_em=hoje,
        )
        for i in range(5)
    ]
    trends_hoje = calculador.calcular_tendencias_video(
        id_canal="UC1",
        id_video="V1",
        tecnica="kmeans",
        topicos_por_comentario={c.id_comentario: "ia" for c in c_hoje},
        comentarios=c_hoje,
        referencia_temporal=hoje,
    )
    assert len(trends_hoje) == 1
    assert trends_hoje[0].data_referencia == "2026-10-14"
    assert trends_hoje[0].status_tendencia == "novo"
    assert trends_hoje[0].percentual_variacao == 100.0

    # Dia 2 (Amanhã): Tópico 'ia' decresce de 5 para 2 (-60%), e surge tópico 'python' novo
    c_amanha = list(c_hoje)  # os mesmos do dia anterior agora caem na janela anterior
    c_amanha.extend([
        ComentarioColetado(
            id_comentario=f"CA_IA_{i}",
            id_video="V1",
            id_canal="UC1",
            id_comentario_pai=None,
            etag="e",
            texto_original=f"Amanha IA {i}",
            hash_conteudo=f"ha_{i}",
            publicado_em=amanha - timedelta(hours=2),
            atualizado_em=amanha - timedelta(hours=2),
            contagem_curtidas=1,
            origem="principal",
            coletado_em=amanha,
        )
        for i in range(2)
    ])
    c_amanha.extend([
        ComentarioColetado(
            id_comentario=f"CA_PY_{i}",
            id_video="V1",
            id_canal="UC1",
            id_comentario_pai=None,
            etag="e",
            texto_original=f"Amanha Python {i}",
            hash_conteudo=f"hp_{i}",
            publicado_em=amanha - timedelta(hours=3),
            atualizado_em=amanha - timedelta(hours=3),
            contagem_curtidas=1,
            origem="principal",
            coletado_em=amanha,
        )
        for i in range(4)
    ])

    mapa_amanha = {}
    for c in c_amanha:
        mapa_amanha[c.id_comentario] = "python" if "PY" in c.id_comentario else "ia"

    trends_amanha = calculador.calcular_tendencias_video(
        id_canal="UC1",
        id_video="V1",
        tecnica="kmeans",
        topicos_por_comentario=mapa_amanha,
        comentarios=c_amanha,
        referencia_temporal=amanha,
    )
    assert len(trends_amanha) == 2
    trends_por_topico = {t.topico: t for t in trends_amanha}

    assert trends_por_topico["ia"].data_referencia == "2026-10-15"
    assert trends_por_topico["ia"].status_tendencia == "decrescendo"
    assert trends_por_topico["ia"].percentual_variacao == -60.0

    assert trends_por_topico["python"].data_referencia == "2026-10-15"
    assert trends_por_topico["python"].status_tendencia == "novo"
    assert trends_por_topico["python"].percentual_variacao == 100.0


def test_modo_irrestrito_todos_comentarios() -> None:
    """Verifica se max_amostras_video=0 e max_amostras_canal=0 preservam todos os comentários sem corte."""
    calculador = CalculadorTendencias(max_amostras_video=0)
    agora = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)

    comentarios: list[ComentarioColetado] = [
        ComentarioColetado(
            id_comentario=f"C_{i}",
            id_video="V_IRRESTRITO",
            id_canal="UC_IRRESTRITO",
            id_comentario_pai=None,
            etag="e",
            texto_original=f"Comentário detalhado número {i}",
            hash_conteudo=f"h_{i}",
            publicado_em=agora - timedelta(minutes=i * 10),
            atualizado_em=agora - timedelta(minutes=i * 10),
            contagem_curtidas=1,
            origem="principal",
            coletado_em=agora,
        )
        for i in range(15)
    ]

    mapa = {c.id_comentario: "automacao" for c in comentarios}
    registros = calculador.calcular_tendencias_video(
        id_canal="UC_IRRESTRITO",
        id_video="V_IRRESTRITO",
        tecnica="kmeans",
        topicos_por_comentario=mapa,
        comentarios=comentarios,
        referencia_temporal=agora,
    )

    assert len(registros) == 1
    amostras = registros[0].comentarios_amostra.split("|||")
    # Todas as 15 mensagens devem estar presentes sem truncamento
    assert len(amostras) == 15
    assert "Comentário detalhado número 0" in amostras
    assert "Comentário detalhado número 14" in amostras

    # Testar agregação no canal com max_amostras_canal=0
    agregador = AgregadorVisoes(max_amostras_canal=0)
    consolidados = agregador.consolidar_canal("UC_IRRESTRITO", "kmeans", registros)
    assert len(consolidados) == 1
    amostras_canal = consolidados[0].comentarios_amostra.split("|||")
    assert len(amostras_canal) == 15

