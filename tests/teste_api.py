"""Testes automatizados para os endpoints REST da aplicação FastAPI."""

from starlette.testclient import TestClient

from app.servico_api.aplicacao_fastapi import criar_aplicacao


def teste_api_endpoint_saude() -> None:
    """Verifica que o endpoint /health retorna status healthy e versão correta."""
    app = criar_aplicacao()
    cliente = TestClient(app)

    resposta = cliente.get("/health")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["status"] == "healthy"
    assert dados["servico"] == "steam-reviews-clustering"
    assert dados["versao"] == "4.1"


def teste_api_endpoint_metricas_prometheus() -> None:
    """Verifica a exportação de métricas em formato Prometheus no endpoint /metrics."""
    app = criar_aplicacao()
    cliente = TestClient(app)

    resposta = cliente.get("/metrics")
    assert resposta.status_code == 200
    assert "text/plain" in resposta.headers.get("content-type", "")
    assert len(resposta.text) > 0


def teste_api_endpoint_clusters_info() -> None:
    """Verifica a consulta estruturada de clusters para um AppID."""
    app = criar_aplicacao()
    cliente = TestClient(app)

    resposta = cliente.get("/api/v1/jogos/427520/clusters")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["appid"] == 427520
    assert dados["total_clusters"] == 3
    assert dados["status"] == "ativo"


def teste_api_endpoint_reviews_consulta_humana() -> None:
    """Verifica a recuperação paginada de avaliações textuais originais para leitura humana."""
    app = criar_aplicacao()
    cliente = TestClient(app)

    resposta = cliente.get("/api/v1/jogos/427520/reviews?cluster_id=0&limite=5")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["appid"] == 427520
    assert dados["total_retornado"] >= 1
    primeira_review = dados["reviews"][0]
    assert primeira_review["cluster_id"] == 0
    assert "review_texto" in primeira_review
    assert len(primeira_review["review_texto"]) > 0


def teste_api_endpoint_predizer_clusters() -> None:
    """Verifica a rota de inferência de partição de clusters."""
    app = criar_aplicacao()
    cliente = TestClient(app)

    payload = {
        "dados_atributos": [
            [10.0, 500.0, 20.0],
            [1.0, 50.0, 0.0],
        ]
    }
    resposta = cliente.post("/api/v1/jogos/427520/predizer", json=payload)
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["appid"] == 427520
    assert len(dados["clusters_atribuidos"]) == 2
