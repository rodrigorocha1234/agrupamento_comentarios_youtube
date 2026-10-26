"""Testes unitários para o módulo de Processamento de Linguagem Natural (PLN)."""

import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans

from app.conf_yaml import (
    ConfigCountInfo,
    ConfigFusaoPLNInfo,
    ConfigPLNInfo,
    ConfigSpacyInfo,
    ConfigTFIDFInfo,
    ConfYAML,
)
from app.excecoes import ErroPreprocessamento
from app.processamento_pln.adaptador_matriz import AdaptadorMatrizPLN
from app.processamento_pln.estrategia_count import EstrategiaTratamentoCount
from app.processamento_pln.estrategia_spacy import EstrategiaTratamentoSpacy
from app.processamento_pln.estrategia_tfidf import EstrategiaTratamentoTFIDF
from app.processamento_pln.fabrica_tratamento_pln import FabricaTratamentoPLN
from app.processamento_pln.fachada_pln import FachadaProcessamentoPLN


def test_estrategia_spacy_processa_textos_com_sucesso() -> None:
    """Verifica que a estratégia spaCy padrão gera embeddings densos dos textos."""
    cfg = ConfigSpacyInfo(
        modelo="pt_core_news_sm",
        remover_stopwords=True,
        lematizar=True,
        remover_pontuacao=True,
        remover_numeros=True,
    )
    estrategia = EstrategiaTratamentoSpacy(cfg)
    textos = [
        "Jogo incrível, gráficos e jogabilidade espetaculares!",
        "Muito ruim, cheio de bugs e travamentos constantes.",
        "",
    ]
    df_vetores = estrategia.processar_textos(textos)

    assert isinstance(df_vetores, pd.DataFrame)
    assert len(df_vetores) == 3
    assert df_vetores.shape[1] > 0
    assert all(col.startswith("spacy_emb_") for col in df_vetores.columns)
    assert df_vetores.dtypes.iloc[0] == np.float64
    assert not df_vetores.isna().any().any()


def test_estrategia_tfidf_processa_textos_com_sucesso() -> None:
    """Verifica vetorização TF-IDF scikit-learn."""
    cfg = ConfigTFIDFInfo(max_features=10, ngram_range=[1, 2])
    estrategia = EstrategiaTratamentoTFIDF(cfg)
    textos = [
        "jogo bom recomendo",
        "jogo ruim pessimo",
        "recomendo muito bom",
    ]
    df_vetores = estrategia.processar_textos(textos)

    assert isinstance(df_vetores, pd.DataFrame)
    assert len(df_vetores) == 3
    assert df_vetores.shape[1] <= 10
    assert all(col.startswith("tfidf_") for col in df_vetores.columns)


def test_estrategia_count_processa_textos_com_sucesso() -> None:
    """Verifica vetorização Count / Bag of Words scikit-learn."""
    cfg = ConfigCountInfo(max_features=5, ngram_range=[1, 1])
    estrategia = EstrategiaTratamentoCount(cfg)
    textos = [
        "otimo jogo suporte rapido",
        "jogo fraco sem conteudo",
    ]
    df_vetores = estrategia.processar_textos(textos)

    assert isinstance(df_vetores, pd.DataFrame)
    assert len(df_vetores) == 2
    assert df_vetores.shape[1] <= 5
    assert all(col.startswith("count_") for col in df_vetores.columns)


def test_fabrica_tratamento_pln_despacha_corretamente() -> None:
    """Verifica a resolução da GoF Factory com match e disparo em estratégia inválida."""
    # spaCy (padrão)
    cfg_spacy = ConfigPLNInfo(tratamento="spacy")
    inst_spacy = FabricaTratamentoPLN.criar_estrategia(cfg_spacy)
    assert isinstance(inst_spacy, EstrategiaTratamentoSpacy)

    # TF-IDF
    cfg_tfidf = ConfigPLNInfo(tratamento="tfidf")
    inst_tfidf = FabricaTratamentoPLN.criar_estrategia(cfg_tfidf)
    assert isinstance(inst_tfidf, EstrategiaTratamentoTFIDF)

    # Count
    cfg_count = ConfigPLNInfo(tratamento="count")
    inst_count = FabricaTratamentoPLN.criar_estrategia(cfg_count)
    assert isinstance(inst_count, EstrategiaTratamentoCount)

    # Tratamento não cadastrado
    cfg_invalido = ConfigPLNInfo.model_construct(tratamento="inexistente")
    with pytest.raises(ErroPreprocessamento, match="não suportado"):
        FabricaTratamentoPLN.criar_estrategia(cfg_invalido)


def test_adaptador_matriz_pln_modos_fusao() -> None:
    """Verifica os modos de fusão ('apenas_texto' e 'concatenar') do GoF Adapter."""
    df_num = pd.DataFrame({"horas": [10.0, 50.0], "votos": [1.0, 5.0]})
    df_txt = pd.DataFrame({"f1": [0.1, 0.2], "f2": [0.3, 0.4]})

    # 1. Modo apenas_texto
    adaptador_texto = AdaptadorMatrizPLN(ConfigFusaoPLNInfo(modo="apenas_texto", prefixo_coluna="pln_"))
    res_texto = adaptador_texto.adaptar_fusao(df_num, df_txt)
    assert list(res_texto.columns) == ["pln_f1", "pln_f2"]
    assert len(res_texto) == 2

    # 2. Modo concatenar
    adaptador_concat = AdaptadorMatrizPLN(ConfigFusaoPLNInfo(modo="concatenar", prefixo_coluna="pln_"))
    res_concat = adaptador_concat.adaptar_fusao(df_num, df_txt)
    assert list(res_concat.columns) == ["horas", "votos", "pln_f1", "pln_f2"]
    assert len(res_concat) == 2


def test_fachada_pln_respeita_flag_habilitado_e_agrupa() -> None:
    """Verifica que a fachada de PLN integra o texto ao agrupamento quando habilitada."""
    df_silver = pd.DataFrame(
        {
            "review": [
                "Melhor jogo que já joguei na Steam!",
                "Completamente injogável, péssimo desempenho.",
                "Excelente experiência coop com amigos.",
                "Pior compra do ano, não recomendo.",
            ]
        }
    )
    df_num = pd.DataFrame({"horas": [100.0, 5.0, 80.0, 2.0]})

    # Caso 1: Desabilitado -> retorna df_num intacto
    fachada_desabilitada = FachadaProcessamentoPLN(ConfigPLNInfo(habilitado=False))
    assert not fachada_desabilitada.habilitado
    matriz_desabilitada = fachada_desabilitada.processar_e_fundir(df_silver, df_num)
    assert matriz_desabilitada.equals(df_num)

    # Caso 2: Habilitado com spaCy -> produz matriz para agrupamento KMeans
    cfg_pln = ConfigPLNInfo(
        habilitado=True,
        tratamento="spacy",
        fusao=ConfigFusaoPLNInfo(modo="apenas_texto"),
    )
    fachada_habilitada = FachadaProcessamentoPLN(cfg_pln)
    matriz_pln = fachada_habilitada.processar_e_fundir(df_silver, df_num)

    assert len(matriz_pln) == 4
    assert all(c.startswith("pln_spacy_emb_") for c in matriz_pln.columns)

    # Executa agrupamento KMeans sobre a matriz gerada por PLN
    modelo = KMeans(n_clusters=2, random_state=42)
    rotulos = modelo.fit_predict(matriz_pln)
    assert len(rotulos) == 4
    assert set(rotulos) == {0, 1}


def test_carregamento_config_pln_yaml() -> None:
    """Garante que pln.yaml é validado e carregado pelo ConfYAML central."""
    conf = ConfYAML.carregar_de_diretorio("config")
    assert hasattr(conf, "pln")
    assert not conf.pln.pln.habilitado  # Por padrão desativado
    assert conf.pln.pln.tratamento == "spacy"
    assert conf.pln.pln.spacy.modelo == "pt_core_news_sm"
    assert conf.pln.pln.fusao.modo == "apenas_texto"
