"""Testes automatizados de validação sintática e estrutural dos dashboards Grafana."""

import json
from pathlib import Path


def teste_validacao_dashboards_grafana() -> None:
    """Garante que todos os dashboards em config_ob/dashboards/ são válidos para Grafana 10+."""
    diretorio_dashboards = Path("config_ob/dashboards")
    assert diretorio_dashboards.exists()

    arquivos_dashboards = list(diretorio_dashboards.glob("*.json"))
    assert len(arquivos_dashboards) >= 3

    uids_esperados = {
        "steam-clusters-monitor",
        "steam-lakehouse-lineage",
        "steam-operacao-pipeline",
    }
    uids_encontrados: set[str] = set()

    for arquivo in arquivos_dashboards:
        conteudo = arquivo.read_text(encoding="utf-8")
        dados = json.loads(conteudo)

        assert isinstance(dados, dict)
        assert "title" in dados and len(dados["title"]) > 0
        assert "uid" in dados
        assert "panels" in dados and isinstance(dados["panels"], list)
        assert len(dados["panels"]) > 0
        assert "schemaVersion" in dados

        uids_encontrados.add(dados["uid"])

        # Validação dos painéis
        for painel in dados["panels"]:
            assert "type" in painel
            assert "gridPos" in painel
            if painel["type"] != "row":
                assert "targets" in painel
                assert isinstance(painel["targets"], list)
                for target in painel["targets"]:
                    assert "expr" in target and len(target["expr"]) > 0

    assert uids_esperados.issubset(uids_encontrados)
