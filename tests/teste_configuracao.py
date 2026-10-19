"""Testes unitários para validação de carregamento do arquivo de configurações."""

from pathlib import Path
import pytest

from app.configuracao_geral.provedor_configuracao import (
    ProvedorConfiguracao,
    ProvedorConfiguracaoErro,
)


def test_carregar_configuracao_sucesso() -> None:
    """Valida o carregamento com sucesso do arquivo real config/entradas.yaml."""
    caminho_yaml = Path(__file__).resolve().parent.parent / "config" / "entradas.yaml"
    provedor = ProvedorConfiguracao(caminho_yaml)
    config = provedor.carregar()

    assert config.projeto.idioma == "pt_BR"
    assert config.coleta.dias_publicacao_atras == 7
    assert config.processamento.spacy_modelo in ["pt_core_news_sm", "pt_core_news_lg"]
    assert config.processamento.stopwords.filtro_centroides == ["que", "com", "para", "uma", "este", "esse", "isso", "por", "mais"]
    assert config.processamento.representacao.sublinear_tf is True
    assert config.processamento.representacao.norma == "l2"
    assert config.processamento.tecnicas.kmeans_ativo is True
    assert config.processamento.tecnicas.kmeans_parametros.max_iter == 300
    assert config.processamento.tecnicas.dbscan_ativo is True
    assert config.processamento.tecnicas.dbscan_parametros.algorithm == "auto"
    assert config.processamento.tecnicas.hdbscan_parametros.cluster_selection_method in ["eom", "leaf"]
    assert config.topicos.limiar_penalizacao_global == 0.35
    assert config.topicos.fator_penalidade == 0.2
    assert config.topicos.rotulo_ruido_padrao == "sem_topico"
    assert config.tendencias.max_amostras_video == 0
    assert config.tendencias.max_amostras_canal == 0
    assert config.persistencia.bucket == "youtube-comentarios"
    assert "{id_canal}" in config.persistencia.padrao_chave_bronze
    assert "{id_video}" in config.persistencia.padrao_chave_prata
    assert "{tecnica}" in config.persistencia.padrao_chave_ouro_video
    assert "consolidado" in config.persistencia.padrao_chave_ouro_consolidado
    assert config.api.porta == 8000
    assert config.api.cors_origens == ["*"]
    assert config.api.top_termos_padrao == 5
    assert config.api.tamanho_pagina_padrao == 10
    assert config.api.tamanho_pagina_maximo == 100


def test_carregar_configuracao_arquivo_inexistente() -> None:
    """Garante que exceção de domínio é levantada quando o arquivo não existe."""
    provedor = ProvedorConfiguracao("caminho_inexistente.yaml")
    with pytest.raises(ProvedorConfiguracaoErro):
        provedor.carregar()


def test_carregar_configuracao_valores_padrao_retrocompatibilidade(tmp_path: Path) -> None:
    """Garante que dicionários YAML sem as novas chaves recebem valores padrão com segurança."""
    yaml_antigo = """
projeto:
  nome: teste_retrocompativel
  idioma: pt_BR
coleta:
  habilitada: true
  periodicidade: diaria
  canais: []
  dias_publicacao_atras: 3
  incluir_respostas: false
  tamanho_pagina: 50
  limite_videos_por_canal: null
  tentativas: 2
  atraso_base_segundos: 1.0
  chave_api_env: KEY
processamento:
  spacy_modelo: pt_core_news_sm
  stopwords:
    usar_spacy: true
    adicionais: []
    preservar: []
  representacao:
    tecnica: tfidf
    min_df: 1
    max_df: 1.0
    ngram_range: [1, 1]
  reducao:
    ativa: false
    tecnica: svd
    componentes: 50
  tecnicas:
    kmeans:
      ativo: true
      parametros: {n_clusters: 3, random_state: 42, n_init: 5}
    dbscan:
      ativo: false
      parametros: {eps: 0.5, min_samples: 3, metric: cosine}
    hdbscan:
      ativo: false
      parametros: {min_cluster_size: 5, min_samples: 3, metric: euclidean}
topicos:
  pos_permitidas: [NOUN]
  comprimento_minimo: 3
  peso_tfidf: 0.8
  peso_frequencia: 0.2
  penalizacao_global: false
tendencias:
  janela_dias: 7
  minimo_comentarios: 3
  crescimento_minimo_proporcao: 0.1
  queda_minima_proporcao: 0.1
persistencia:
  tipo: s3
  bucket: bucket-antigo
  prefixos: {bronze: b, prata: p, ouro: o}
  endpoint_env: S3_URL
  access_key_env: ACCESS
  secret_key_env: SECRET
mlflow:
  tracking_uri_env: MLFLOW_TRACKING_URI
  serving_url_env: MLFLOW_SERVING_URL
api:
  porta: 8080
  tempo_limite_segundos: 15.0
observabilidade:
  prometheus: false
  grafana: false
  labels_alta_cardinalidade: false
"""
    arquivo_temp = tmp_path / "entradas_antigo.yaml"
    arquivo_temp.write_text(yaml_antigo, encoding="utf-8")

    config = ProvedorConfiguracao(arquivo_temp).carregar()

    assert config.processamento.stopwords.filtro_centroides == []
    assert config.processamento.representacao.sublinear_tf is True
    assert config.processamento.representacao.norma == "l2"
    assert config.processamento.tecnicas.kmeans_parametros.max_iter == 300
    assert config.processamento.tecnicas.dbscan_parametros.algorithm == "auto"
    assert config.processamento.tecnicas.hdbscan_parametros.cluster_selection_method == "eom"
    assert config.topicos.limiar_penalizacao_global == 0.75
    assert config.topicos.fator_penalidade == 0.2
    assert config.topicos.rotulo_ruido_padrao == "sem_topico"
    assert config.tendencias.max_amostras_video == 5
    assert config.tendencias.max_amostras_canal == 10
    assert config.api.cors_origens == ["*"]
    assert config.api.top_termos_padrao == 5
    assert config.api.tamanho_pagina_padrao == 10
    assert config.api.tamanho_pagina_maximo == 100

