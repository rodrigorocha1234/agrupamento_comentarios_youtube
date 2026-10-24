"""Testes para a fachada ConfYAML e modelos de validação de configuração."""

import pytest
from pydantic import ValidationError

from app.configuracao_geral.conf_yaml import ConfYAML
from app.configuracao_geral.validador_compatibilidade import (
    ValidadorCompatibilidade,
)


def teste_carregamento_conf_yaml() -> None:
    """Verifica se ConfYAML carrega e tipa todos os arquivos padrão com sucesso."""
    conf = ConfYAML()

    assert conf.projeto.configuracao.nome_projeto == "steam_reviews_clustering"
    assert conf.projeto.funcionalidades.processamento_linguagem_natural is False
    assert conf.projeto.funcionalidades.analise_temporal is False
    assert len(conf.steam.steam.jogos) >= 2
    assert conf.staging.staging.tecnologia == "sqlite"
    assert conf.fluxos_incrementais.fluxos_incrementais.paginacao.tamanho_pagina == 100
    assert len(conf.hash_configuracao) == 64


def teste_validador_compatibilidade_sucesso() -> None:
    """Verifica que a configuração padrão atende a todas as regras cruzadas."""
    conf = ConfYAML()
    validador = ValidadorCompatibilidade(conf)
    validador.validar_todas_regras()


def teste_rejeicao_campos_desconhecidos_extra_forbid() -> None:
    """Garante que campos não declarados no schema sejam estritamente proibidos."""
    from app.configuracao_geral.modelos_configuracao import MetadadosProjeto

    with pytest.raises(ValidationError):
        MetadadosProjeto.model_validate(
            {"versao_schema": "1.0", "nome_projeto": "teste", "campo_fantasma": 123}
        )
