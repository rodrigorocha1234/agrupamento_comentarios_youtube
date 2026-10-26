"""Testes unitários para o módulo conf_yaml e validação das regras arquiteturais."""

import os
from pathlib import Path

import pytest

from app.conf_yaml import (
    ConfigItemColuna,
    ConfYAML,
    expandir_variaveis_ambiente,
)
from app.contratos.fonte_dados import ProtocoloFonteDados
from app.contratos.motor_clustering import ProtocoloMotorClustering
from app.contratos.motor_processamento import ProtocoloMotorProcessamento
from app.contratos.observador import ProtocoloObservadorExperimento
from app.contratos.repositorio import ProtocoloRepositorioLakehouse
from app.excecoes import ErroConfiguracao


def test_carregar_configuracao_padrao_valida() -> None:
    """Valida o carregamento dos 13 arquivos YAML existentes no repositório."""
    caminho_config = Path("config")
    conf = ConfYAML.carregar_de_diretorio(caminho_config)

    assert conf.projeto.projeto.nome == "steam_reviews_clustering"
    assert not conf.projeto.funcionalidades.pln.habilitado
    assert conf.clustering.clustering.algoritmo in {"kmeans", "dbscan", "hdbscan"}
    assert conf.processamento.processamento.motor == "pandas"
    assert "recommendationid" in conf.atributos.atributos.identificadores
    assert "recommendationid" not in conf.atributos.atributos.treino.colunas
    assert not conf.atributos.atributos.texto.incluir_no_treino
    assert conf.datalake.datalake.tipo in {"s3", "rustfs"}
    assert conf.datalake.datalake.bucket == "steam-reviews"
    assert conf.datalake.datalake.caminho == "datalake"
    assert conf.datalake.datalake.bronze.prefixo == "bronze"
    assert conf.datalake.datalake.bronze.caminho == "bronze"
    assert conf.datalake.datalake.silver.prefixo == "silver"
    assert conf.datalake.datalake.silver.caminho == "silver"
    assert conf.datalake.datalake.gold.prefixo == "gold"
    assert conf.datalake.datalake.gold.caminho == "gold"
    assert conf.cadastro_projeto.cadastro_projeto.id_projeto == "steam_reviews_clustering"
    assert conf.cadastro_projeto.cadastro_projeto.entidade == "avaliacao"
    assert conf.cadastro_projeto.cadastro_projeto.mapeamento_origem.identificador_primario == "recommendationid"
    # Validação da seleção de colunas desabilitada por padrão
    assert not conf.processamento.processamento.selecao_colunas.habilitado
    assert len(conf.processamento.processamento.selecao_colunas.colunas) > 0
    assert all(
        isinstance(col, ConfigItemColuna) and not col.habilitado
        for col in conf.processamento.processamento.selecao_colunas.colunas
    )


def test_expansao_variaveis_ambiente() -> None:
    """Verifica a expansão de variáveis com e sem valor padrão."""
    os.environ["TESTE_VAR_STEAM"] = "valor_ativo"
    texto = "chave: ${TESTE_VAR_STEAM} e padrao: ${VAR_INEXISTENTE:-padrao_ok}"
    resultado = expandir_variaveis_ambiente(texto)
    assert resultado == "chave: valor_ativo e padrao: padrao_ok"


def test_rejeicao_identificador_na_matriz_treino(tmp_path: Path) -> None:
    """Valida que identificadores na matriz de treino disparam ErroConfiguracao."""
    caminho_config = Path("config")
    # Copia configurações para diretório temporário
    for f in caminho_config.glob("*.yaml"):
        (tmp_path / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")

    # Injeta 'recommendationid' nas colunas de treino
    arquivo_atributos = tmp_path / "atributos.yaml"
    conteudo = arquivo_atributos.read_text(encoding="utf-8")
    conteudo_invalido = conteudo.replace(
        "    colunas:\n      - num_reviews",
        "    colunas:\n      - recommendationid\n      - num_reviews",
    )
    arquivo_atributos.write_text(conteudo_invalido, encoding="utf-8")

    with pytest.raises(ErroConfiguracao, match="Identificadores não podem fazer parte dos atributos de treino"):
        ConfYAML.carregar_de_diretorio(tmp_path)


def test_rejeicao_pln_desabilitado_com_texto_em_treino(tmp_path: Path) -> None:
    """Valida que texto de review no treino é bloqueado quando PLN está desligado."""
    caminho_config = Path("config")
    for f in caminho_config.glob("*.yaml"):
        (tmp_path / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")

    arquivo_atributos = tmp_path / "atributos.yaml"
    conteudo = arquivo_atributos.read_text(encoding="utf-8")
    conteudo_invalido = conteudo.replace(
        "incluir_no_treino: false",
        "incluir_no_treino: true",
    )
    arquivo_atributos.write_text(conteudo_invalido, encoding="utf-8")

    with pytest.raises(ErroConfiguracao, match="funcionalidades.pln.habilitado é False"):
        ConfYAML.carregar_de_diretorio(tmp_path)


def test_falha_quando_arquivo_obrigatorio_ausente(tmp_path: Path) -> None:
    """Valida que a ausência de um dos 13 arquivos obrigatórios dispara ErroConfiguracao."""
    with pytest.raises(ErroConfiguracao, match="Arquivo obrigatório de configuração ausente"):
        ConfYAML.carregar_de_diretorio(tmp_path)


def test_falha_quando_diretorio_inexistente() -> None:
    """Valida que diretório inexistente dispara ErroConfiguracao."""
    with pytest.raises(ErroConfiguracao, match="Diretório de configuração não encontrado"):
        ConfYAML.carregar_de_diretorio("caminho_que_nao_existe_12345")


def test_protocolos_runtime_checkable() -> None:
    """Verifica se os protocolos são runtime checkable e exportáveis."""
    assert isinstance(ProtocoloFonteDados, type)
    assert isinstance(ProtocoloMotorProcessamento, type)
    assert isinstance(ProtocoloMotorClustering, type)
    assert isinstance(ProtocoloRepositorioLakehouse, type)
    assert isinstance(ProtocoloObservadorExperimento, type)


def test_extensibilidade_para_outro_projeto(tmp_path: Path) -> None:
    """Verifica que outro projeto (ex: comentários do YouTube) pode ser registrado e validado sem alterar o código Python."""
    caminho_config = Path("config")
    for f in caminho_config.glob("*.yaml"):
        (tmp_path / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")

    # Altera cadastro_projeto.yaml para comentários do YouTube
    novo_cadastro = """cadastro_projeto:
  id_projeto: youtube_comentarios_clustering
  nome: "Agrupamento de Comentários do YouTube"
  descricao: "Segmentação não supervisionada de comentários de canais"
  versao: "1.0.0"
  dominio: "midia_social"
  entidade: "comentario"
  mapeamento_origem:
    tipo_fonte: api_rest
    identificador_primario: comment_id
    identificador_contexto: video_id
    campo_texto_consulta: texto_comentario
    campos_numericos_padrao:
      - like_count
      - reply_count
  infraestrutura:
    datalake_bucket: youtube-comentarios
    mlflow_experimento: youtube_comments_clustering
"""
    (tmp_path / "cadastro_projeto.yaml").write_text(novo_cadastro, encoding="utf-8")

    conf = ConfYAML.carregar_de_diretorio(tmp_path)
    assert conf.cadastro_projeto.cadastro_projeto.id_projeto == "youtube_comentarios_clustering"
    assert conf.cadastro_projeto.cadastro_projeto.entidade == "comentario"
    assert conf.cadastro_projeto.cadastro_projeto.mapeamento_origem.identificador_primario == "comment_id"
    assert conf.cadastro_projeto.cadastro_projeto.infraestrutura.datalake_bucket == "youtube-comentarios"
