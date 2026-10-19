"""Testes unitários rigorosos para a fase de NLP e representação vetorial."""

from app.representacao_texto.redutor_dimensionalidade import (
    RedutorDimensionalidade,
)
from app.representacao_texto.vetorizador_tfidf import VetorizadorTfidf
from app.tratamento_texto.lematizador_spacy import LematizadorSpacy
from app.tratamento_texto.limpador_texto import LimpadorTexto
from app.tratamento_texto.rotulador_topicos import RotuladorTopicos


def test_limpador_texto_remove_links_e_mencoes() -> None:
    """Verifica remoção de URLs e tags sem perder o texto original."""
    texto = "Olha esse vídeo https://youtube.com/xyz muito bom @usuario_teste!!!"
    limpo = LimpadorTexto.normalizar(texto)
    assert "https://" not in limpo
    assert "@usuario_teste" not in limpo
    assert "vídeo" in limpo
    assert "muito bom" in limpo


def test_lematizador_preserva_negacoes_e_filtra_pos() -> None:
    """Valida que termos de negação configurados não são descartados como stopwords."""
    lematizador = LematizadorSpacy(
        modelo_nome="pt_core_news_sm",
        preservar_negacoes=["nao", "não", "nunca", "sem"],
        pos_permitidas=["NOUN", "PROPN", "ADJ"],
    )
    texto = "Eu não gostei deste produto ruim mas a entrega foi rápida."
    lemas = lematizador.processar_texto(texto)

    # Negação deve ser preservada
    assert any(n in lemas for n in ["nao", "não"])
    # Adjetivos e substantivos devem estar presentes
    assert any(p in lemas for p in ["produto", "entrega", "ruim", "rápido", "rapido"])


def test_rotulador_topicos_elege_um_lema_ou_sem_topico() -> None:
    """Garante que o rotulador extrai exatamente 1 lema e gera 'sem_topico' se vazio."""
    rotulador = RotuladorTopicos(peso_tfidf=0.7, peso_frequencia=0.3)

    cluster_python = [
        ["programacao", "python", "codigo"],
        ["python", "linguagem", "software"],
        ["desenvolvimento", "python"],
    ]
    globais = cluster_python + [
        ["culinaria", "receita", "bolo"],
        ["receita", "sobremesa"],
    ]

    topico = rotulador.rotular_cluster(cluster_python, globais)
    assert topico == "python"

    # Caso vazio
    topico_vazio = rotulador.rotular_cluster([], globais)
    assert topico_vazio == "sem_topico"


def test_vetorizador_tfidf_e_redutor_svd() -> None:
    """Testa a geração de matriz esparsa TF-IDF e redução dimensional."""
    vetorizador = VetorizadorTfidf(min_df=1, max_df=1.0, ngram_range=(1, 2))
    textos = [
        "inteligencia artificial aplicada",
        "redes neurais e inteligencia artificial",
        "aprendizado de maquina supervisionado",
    ]
    matriz = vetorizador.ajustar_e_transformar(textos)
    shape_matriz = matriz.shape
    assert shape_matriz is not None
    assert shape_matriz[0] == 3
    assert shape_matriz[1] > 0
    assert "inteligencia" in vetorizador.obter_nomes_caracteristicas()

    redutor = RedutorDimensionalidade(componentes=2)
    matriz_reduzida = redutor.ajustar_e_reduzir(matriz)
    formato = matriz_reduzida.shape
    assert formato is not None
    assert formato[0] == 3
    assert formato[1] <= 2


def test_extrator_embeddings_normalizacao_l2() -> None:
    """Verifica que o extrator de embeddings gera matriz densa com norma unitária L2."""
    from app.representacao_texto.extrator_embeddings import ExtratorEmbeddings
    import numpy as np

    extrator = ExtratorEmbeddings(modelo_nome="pt_core_news_sm", norma="l2")
    textos = [
        "ótimo vídeo sobre ciência de dados",
        "conteúdo excelente e didática perfeita",
        "programação em python avançada",
    ]
    matriz = extrator.extrair_vetores(textos)
    assert isinstance(matriz, np.ndarray)
    assert matriz.shape[0] == 3
    assert matriz.shape[1] > 0

    # Verifica norma L2 próxima de 1.0 para cada linha não nula
    normas = np.linalg.norm(matriz, axis=1)
    for norma in normas:
        assert np.isclose(norma, 1.0, atol=1e-4)


def test_extrator_bertimbau_normalizacao_l2_e_lazy_loading() -> None:
    """Valida o ExtratorBertimbau com fallback, normalização L2 e textos vazios."""
    import numpy as np
    from unittest.mock import MagicMock
    from app.representacao_texto.extrator_bertimbau import ExtratorBertimbau

    extrator = ExtratorBertimbau(
        modelo_nome="neuralmind/bert-base-portuguese-cased",
        dispositivo="cpu",
        batch_size=16,
        norma="l2",
    )

    # 1. Caso lista vazia
    matriz_vazia = extrator.extrair_vetores([])
    assert matriz_vazia.shape == (0, 0)

    # 2. Mock do modelo SentenceTransformer para isolamento do teste unitário
    mock_modelo = MagicMock()
    # Retorna vetores sintéticos 768d para 3 amostras
    vetores_sinteticos = np.random.RandomState(42).randn(3, 768)
    mock_modelo.encode.return_value = vetores_sinteticos

    extrator = ExtratorBertimbau(
        modelo_nome="neuralmind/bert-base-portuguese-cased",
        dispositivo="cpu",
        batch_size=16,
        norma="l2",
        modelo_precarregado=mock_modelo,
    )

    textos = [
        "excelente vídeo de inteligência artificial",
        "",  # texto em branco deve ser zerado
        "comentário sobre gameplay e mods",
    ]

    matriz = extrator.extrair_vetores(textos)
    assert isinstance(matriz, np.ndarray)
    assert matriz.shape == (3, 768)

    # Linha 1 e 3 devem ter norma L2 == 1.0
    assert np.isclose(np.linalg.norm(matriz[0]), 1.0, atol=1e-4)
    assert np.isclose(np.linalg.norm(matriz[2]), 1.0, atol=1e-4)

    # Linha 2 (vazio) deve ser zero
    assert np.all(matriz[1] == 0.0)


def test_fabrica_representacao_cria_extrator_bertimbau() -> None:
    """Verifica instanciação configurada de ExtratorBertimbau via fábrica."""
    from pathlib import Path
    from app.configuracao_geral.provedor_configuracao import ProvedorConfiguracao
    from app.representacao_texto.fabrica_representacao import FabricaRepresentacao
    from app.representacao_texto.extrator_bertimbau import ExtratorBertimbau

    caminho_yaml = Path(__file__).resolve().parent.parent / "config" / "entradas.yaml"
    provedor = ProvedorConfiguracao(caminho_yaml)
    config = provedor.carregar()

    extrator = FabricaRepresentacao.criar_extrator_bertimbau(config.processamento)
    assert isinstance(extrator, ExtratorBertimbau)
    assert extrator.modelo_nome == "neuralmind/bert-base-portuguese-cased"
    assert extrator.dispositivo == "cpu"
    assert extrator.batch_size == 32


def test_redutor_umap_ajuste_reducao_e_normalizacao() -> None:
    """Verifica redução não-linear UMAP com normalização L2 e proteção de pequenas amostras."""
    import numpy as np
    from app.representacao_texto.redutor_umap import RedutorUmap

    redutor = RedutorUmap(
        componentes=3,
        n_vizinhos=5,
        distancia_minima=0.0,
        metrica="cosine",
        random_state=42,
        norma="l2",
    )

    # 1. Matriz sintética com 10 amostras e 50 dimensões
    rng = np.random.RandomState(42)
    matriz_teste = rng.randn(10, 50)
    matriz_reduzida = redutor.ajustar_e_reduzir(matriz_teste)

    assert isinstance(matriz_reduzida, np.ndarray)
    assert matriz_reduzida.shape[0] == 10
    assert matriz_reduzida.shape[1] <= 3

    # Norma L2 deve ser 1.0
    for linha in matriz_reduzida:
        assert np.isclose(np.linalg.norm(linha), 1.0, atol=1e-4)

    # 2. Teste de projeção em novos dados
    novos_dados = rng.randn(2, 50)
    projetados = redutor.reduzir(novos_dados)
    assert projetados.shape == (2, matriz_reduzida.shape[1])

    # 3. Teste de proteção com menos de 4 amostras
    matriz_pequena = rng.randn(2, 50)
    redutor_defensivo = RedutorUmap(componentes=5)
    resultado_pequeno = redutor_defensivo.ajustar_e_reduzir(matriz_pequena)
    assert resultado_pequeno.shape == (2, 50)


def test_fabrica_representacao_cria_redutor_umap() -> None:
    """Valida instanciação do RedutorUmap através de FabricaRepresentacao."""
    from pathlib import Path
    from app.configuracao_geral.provedor_configuracao import ProvedorConfiguracao
    from app.representacao_texto.fabrica_representacao import FabricaRepresentacao
    from app.representacao_texto.redutor_umap import RedutorUmap

    caminho_yaml = Path(__file__).resolve().parent.parent / "config" / "entradas.yaml"
    provedor = ProvedorConfiguracao(caminho_yaml)
    config = provedor.carregar()

    redutor = FabricaRepresentacao.criar_redutor_opcional(config.processamento)
    assert isinstance(redutor, RedutorUmap)
    assert redutor.componentes == 5
    assert redutor.n_vizinhos == 15
    assert redutor.metrica == "cosine"



