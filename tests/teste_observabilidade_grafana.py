"""Testes unitários para isolamento, protocolo e fábrica do provedor Grafana."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from app.coleta_metricas.fabrica_visualizacao import FabricaProvedorVisualizacao
from app.coleta_metricas.protocolo_visualizacao import ProtocoloProvedorVisualizacao
from app.coleta_metricas.provedor_grafana import ProvedorVisualizacaoGrafana
from app.coleta_metricas.provedor_nulo import ProvedorVisualizacaoNulo
from app.configuracao_geral.modelos_configuracao import ConfiguracaoObservabilidade
from app.configuracao_geral.provedor_configuracao import ProvedorConfiguracao
from app.configuracao_geral.tipos_enumerados import TipoProvedorVisualizacao


def test_provedor_grafana_contrato_e_urls() -> None:
    """Valida que ProvedorVisualizacaoGrafana implementa ProtocoloProvedorVisualizacao."""
    provedor = ProvedorVisualizacaoGrafana("http://localhost:3000/")
    assert isinstance(provedor, ProtocoloProvedorVisualizacao)
    assert provedor.tipo_provedor == TipoProvedorVisualizacao.GRAFANA
    assert provedor.url_base == "http://localhost:3000"

    url_pipe = provedor.obter_url_dashboard("yt-pipe-operacional")
    assert url_pipe == "http://localhost:3000/d/yt-pipe-operacional/pipeline-operacional-and-ingestao-youtube"

    url_lake = provedor.obter_url_dashboard("yt-datalake-lakehouse")
    assert url_lake == "http://localhost:3000/d/yt-datalake-lakehouse/data-lakehouse-and-armazenamento-s3-rustfs"

    url_api = provedor.obter_url_dashboard("yt-api-fastapi")
    assert url_api == "http://localhost:3000/d/yt-api-fastapi/api-fastapi-and-serving-operacional"

    url_clusters = provedor.obter_url_dashboard("yt-clusters-modelos")
    assert url_clusters == "http://localhost:3000/d/yt-clusters-modelos/qualidade-de-agrupamento-and-modelos-de-ml"

    url_desconhecido = provedor.obter_url_dashboard("dashboard-customizado")
    assert url_desconhecido == "http://localhost:3000/d/dashboard-customizado"


def test_provedor_grafana_listar_e_metadados() -> None:
    """Valida a listagem e obtenção de metadados dos painéis."""
    provedor = ProvedorVisualizacaoGrafana("http://grafana:3000")
    dashboards = provedor.listar_dashboards()
    assert len(dashboards) == 4
    uids = {d["uid"] for d in dashboards}
    assert uids == {
        "yt-pipe-operacional",
        "yt-datalake-lakehouse",
        "yt-api-fastapi",
        "yt-clusters-modelos",
    }

    meta = provedor.obter_metadados_painel("yt-api-fastapi")
    assert meta["status"] == "provisionado"
    assert "FastAPI" in meta["titulo"]

    meta_outro = provedor.obter_metadados_painel("painel-inexistente")
    assert meta_outro["status"] == "personalizado_ou_desconhecido"


def test_provedor_grafana_disponibilidade_mock() -> None:
    """Valida verificação de integridade da API Grafana (/api/health)."""
    provedor = ProvedorVisualizacaoGrafana("http://localhost:3000")

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.read.return_value = b'{"database": "ok", "version": "11.1.0"}'

    with patch("urllib.request.urlopen", return_value=mock_resp):
        assert provedor.verificar_disponibilidade() is True

    with patch("urllib.request.urlopen", side_effect=TimeoutError()):
        assert provedor.verificar_disponibilidade() is False



def test_provedor_nulo() -> None:
    """Valida comportamento seguro da classe ProvedorVisualizacaoNulo."""
    nulo = ProvedorVisualizacaoNulo()
    assert isinstance(nulo, ProtocoloProvedorVisualizacao)
    assert nulo.tipo_provedor == TipoProvedorVisualizacao.NENHUM
    assert nulo.verificar_disponibilidade() is False
    assert nulo.obter_url_dashboard("yt-pipe-operacional") == ""
    assert nulo.listar_dashboards() == []


def test_fabrica_provedor_visualizacao() -> None:
    """Valida instanciação polimórfica e extensibilidade da FabricaProvedorVisualizacao."""
    config_grafana = ConfiguracaoObservabilidade(
        prometheus=True,
        grafana=True,
        labels_alta_cardinalidade=False,
        provedor_visualizacao=TipoProvedorVisualizacao.GRAFANA,
        url_visualizacao="http://localhost:3000",
    )
    instancia = FabricaProvedorVisualizacao.criar_provedor(config_grafana)
    assert isinstance(instancia, ProvedorVisualizacaoGrafana)

    config_desativado = ConfiguracaoObservabilidade(
        prometheus=True,
        grafana=False,
        labels_alta_cardinalidade=False,
        provedor_visualizacao=TipoProvedorVisualizacao.GRAFANA,
    )
    instancia_desativada = FabricaProvedorVisualizacao.criar_provedor(config_desativado)
    assert isinstance(instancia_desativada, ProvedorVisualizacaoNulo)

    config_nenhum = ConfiguracaoObservabilidade(
        prometheus=True,
        grafana=False,
        labels_alta_cardinalidade=False,
        provedor_visualizacao=TipoProvedorVisualizacao.NENHUM,
    )
    instancia_nenhum = FabricaProvedorVisualizacao.criar_provedor(config_nenhum)
    assert isinstance(instancia_nenhum, ProvedorVisualizacaoNulo)

    # Teste de registro de provedor alternativo customizado
    mock_provedor_custom = MagicMock(spec=ProtocoloProvedorVisualizacao)
    FabricaProvedorVisualizacao.registrar_provedor(
        TipoProvedorVisualizacao.CUSTOM, lambda _url: mock_provedor_custom
    )

    config_custom = ConfiguracaoObservabilidade(
        prometheus=True,
        grafana=True,
        labels_alta_cardinalidade=False,
        provedor_visualizacao=TipoProvedorVisualizacao.CUSTOM,
    )
    instancia_custom = FabricaProvedorVisualizacao.criar_provedor(config_custom)
    assert instancia_custom is mock_provedor_custom


def test_carregamento_configuracao_yaml_provedor_visualizacao() -> None:
    """Valida se o ProvedorConfiguracao carrega corretamente os campos de visualização dos arquivos YAML."""
    caminho_base = Path(__file__).resolve().parent.parent / "config"
    provedor = ProvedorConfiguracao(caminho_base / "entradas.yaml")
    config = provedor.carregar()
    assert config.observabilidade.provedor_visualizacao == TipoProvedorVisualizacao.GRAFANA
    assert config.observabilidade.url_visualizacao == "http://localhost:3000"

    provedor_tabular = ProvedorConfiguracao(caminho_base / "entradas_tabular_exemplo.yaml")
    config_tabular = provedor_tabular.carregar()
    assert config_tabular.observabilidade.provedor_visualizacao == TipoProvedorVisualizacao.GRAFANA
