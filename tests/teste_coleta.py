from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import pytest
import requests

from app.coleta_youtube.cliente_youtube import ClienteYouTube
from app.coleta_youtube.extrator_comentarios import ExtratorComentarios
from app.coleta_youtube.tratador_erros import (
    ChaveApiAusenteErro,
    QuotaExcedidaErro,
)


class RespostaFalsa(requests.Response):
    """Subclasse customizada de Response para testes sem tocar em atributos protegidos."""

    def __init__(self, status_code: int, corpo: dict[str, object]) -> None:
        super().__init__()
        self.status_code = status_code
        self._corpo = corpo

    def json(self, **kwargs: object) -> dict[str, object]:
        return self._corpo

    @property
    def text(self) -> str:
        return json.dumps(self._corpo)


class SessaoHttpFalsa:
    """Mock estrutural aderente ao ProtocoloRequisitorHttp para simulações determinísticas."""

    def __init__(self, respostas_por_url: dict[str, tuple[int, dict[str, object]]]) -> None:
        self.respostas_por_url = respostas_por_url
        self.requisicoes_feitas: list[dict[str, object]] = []

    def get(
        self,
        url: str | bytes,
        *,
        params: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> requests.Response:
        url_str = url.decode("utf-8") if isinstance(url, bytes) else url
        self.requisicoes_feitas.append({"url": url_str, "params": params, "timeout": timeout})

        codigo_status, corpo = self.respostas_por_url.get(
            url_str, (404, {"error": {"message": "Nao encontrado"}})
        )
        return RespostaFalsa(status_code=codigo_status, corpo=corpo)


def test_chave_api_vazia_lanca_excecao() -> None:
    """Valida que chave de API vazia gera erro de domínio."""
    with pytest.raises(ChaveApiAusenteErro):
        ClienteYouTube(chave_api="   ")


def test_obter_id_playlist_uploads_sucesso() -> None:
    """Testa resolução correta da playlist de uploads a partir de channels.list."""
    dados_canal: dict[str, object] = {
        "items": [
            {
                "contentDetails": {
                    "relatedPlaylists": {"uploads": "UU_CANAL_TESTE_UPLOADS"}
                }
            }
        ]
    }
    mock_http = SessaoHttpFalsa(
        {"https://www.googleapis.com/youtube/v3/channels": (200, dados_canal)}
    )
    cliente = ClienteYouTube(chave_api="CHAVE_VALIDA", sessao_http=mock_http)
    playlist_id = cliente.obter_id_playlist_uploads("UC_TESTE")
    assert playlist_id == "UU_CANAL_TESTE_UPLOADS"


def test_listar_comentarios_e_respostas_com_paginacao() -> None:
    """Valida coleta exaustiva de commentThreads e de comments (respostas) com paginação."""
    data_recente = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    dados_canal: dict[str, object] = {
        "items": [
            {"contentDetails": {"relatedPlaylists": {"uploads": "UU_PLAYLIST"}}}
        ]
    }
    dados_playlist: dict[str, object] = {
        "items": [
            {
                "contentDetails": {
                    "videoId": "VID_01",
                    "videoPublishedAt": data_recente,
                },
                "snippet": {
                    "title": "Video de Teste",
                    "publishedAt": data_recente,
                },
            }
        ]
    }
    dados_threads: dict[str, object] = {
        "items": [
            {
                "id": "COMM_TOP_1",
                "etag": "etag_1",
                "snippet": {
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": "Excelente video explicativo!",
                            "publishedAt": data_recente,
                            "updatedAt": data_recente,
                            "likeCount": 15,
                        }
                    }
                },
            }
        ]
    }
    dados_respostas: dict[str, object] = {
        "items": [
            {
                "id": "COMM_REPLY_1",
                "etag": "etag_reply_1",
                "snippet": {
                    "textOriginal": "Concordo plenamente com a explicacao.",
                    "publishedAt": data_recente,
                    "updatedAt": data_recente,
                    "likeCount": 3,
                },
            }
        ]
    }

    mock_http = SessaoHttpFalsa(
        {
            "https://www.googleapis.com/youtube/v3/channels": (200, dados_canal),
            "https://www.googleapis.com/youtube/v3/playlistItems": (200, dados_playlist),
            "https://www.googleapis.com/youtube/v3/commentThreads": (200, dados_threads),
            "https://www.googleapis.com/youtube/v3/comments": (200, dados_respostas),
        }
    )

    cliente = ClienteYouTube(chave_api="CHAVE_VALIDA", sessao_http=mock_http)
    extrator = ExtratorComentarios(cliente)

    videos, comentarios = extrator.extrair_canal_completo(
        id_canal="UC_TESTE",
        dias_retroativos=7,
        incluir_respostas=True,
    )

    assert len(videos) == 1
    assert videos[0].id_video == "VID_01"
    assert len(comentarios) == 2

    top_comm = comentarios[0]
    assert top_comm.id_comentario == "COMM_TOP_1"
    assert top_comm.id_comentario_pai is None
    assert top_comm.origem == "principal"
    assert top_comm.contagem_curtidas == 15
    assert len(top_comm.hash_conteudo) == 64

    reply_comm = comentarios[1]
    assert reply_comm.id_comentario == "COMM_REPLY_1"
    assert reply_comm.id_comentario_pai == "COMM_TOP_1"
    assert reply_comm.origem == "resposta"
    assert reply_comm.contagem_curtidas == 3


def test_comentarios_desativados_retorna_vazio() -> None:
    """Garante que vídeos com commentsDisabled retornam lista vazia sem quebrar o fluxo."""
    dados_erro: dict[str, object] = {
        "error": {
            "code": 403,
            "message": "The video has disabled comments.",
            "errors": [{"reason": "commentsDisabled"}],
        }
    }
    mock_http = SessaoHttpFalsa(
        {"https://www.googleapis.com/youtube/v3/commentThreads": (403, dados_erro)}
    )
    cliente = ClienteYouTube(chave_api="CHAVE_VALIDA", sessao_http=mock_http)
    comentarios = cliente.listar_comentarios_principais("VID_BLOQUEADO", "UC_TESTE")
    assert comentarios == []


def test_quota_excedida_lanca_excecao_especifica() -> None:
    """Garante que quotaExceeded levanta QuotaExcedidaErro com retry defensivo."""
    dados_erro: dict[str, object] = {
        "error": {
            "code": 403,
            "message": "The request cannot be completed because you have exceeded your quota.",
            "errors": [{"reason": "quotaExceeded"}],
        }
    }
    mock_http = SessaoHttpFalsa(
        {"https://www.googleapis.com/youtube/v3/channels": (403, dados_erro)}
    )
    cliente = ClienteYouTube(
        chave_api="CHAVE_VALIDA",
        tentativas=1,
        sessao_http=mock_http,
    )
    with pytest.raises(QuotaExcedidaErro):
        cliente.obter_id_playlist_uploads("UC_TESTE")


def test_extrator_arquivo_local_e_fabrica_fontes(tmp_path: Path) -> None:
    """Valida o carregamento polimórfico de fontes locais (CSV) via Adapter e Factory."""
    import pandas as pd
    from app.coleta_youtube.extrator_arquivo_local import ExtratorArquivoLocal
    from app.coleta_youtube.fabrica_fontes import FabricaFontesDados
    from app.configuracao_geral.modelos_configuracao import (
        ConfiguracaoColeta,
        ConfiguracaoGlobal,
        ConfiguracaoProcessamento,
        ConfiguracaoProjeto,
        ConfiguracaoReducao,
        ConfiguracaoTecnicas,
        ConfiguracaoTopicos,
        ConfiguracaoTendencias,
        ConfiguracaoPersistencia,
        ConfiguracaoMLflow,
        ConfiguracaoAPI,
        ConfiguracaoObservabilidade,
        ParametrosDBSCAN,
        ParametrosHDBSCAN,
        ParametrosKMeans,
    )
    from app.configuracao_geral.tipos_enumerados import (
        AlgoritmoVizinhos,
        TipoFonteDados,
        TipoPersistencia,
        TecnicaReducao,
        InicializacaoKMeans,
        MetricaDistancia,
        MetodoSelecaoCluster,
    )
    from app.orquestracao_pipeline.protocolos_ciclo import ProtocoloExtratorComentarios

    # Cria CSV de teste
    csv_file = tmp_path / "comentarios_teste.csv"
    df = pd.DataFrame({
        "id": ["c1", "c2", "c3"],
        "texto": ["Adorei o vídeo!", "Muito bom", "Poderia ser melhor"],
        "curtidas": [10, 5, 1],
        "id_video": ["v1", "v1", "v2"],
    })
    df.to_csv(csv_file, index=False)

    config_coleta = ConfiguracaoColeta(
        habilitada=True,
        fonte=TipoFonteDados.CSV,
        caminho_dados=str(csv_file),
        coluna_texto="texto",
        coluna_id="id",
    )

    # 1. Teste direto do Adaptador
    extrator_local = ExtratorArquivoLocal(config_coleta)
    assert isinstance(extrator_local, ProtocoloExtratorComentarios)

    videos, comentarios = extrator_local.extrair_canal_completo("canal_local")
    assert len(videos) == 2
    assert len(comentarios) == 3
    assert comentarios[0].texto_original == "Adorei o vídeo!"
    assert comentarios[0].id_comentario == "c1"
    nome_canal, _ = extrator_local.obter_detalhes_canal("canal_local")
    assert "Fonte Local" in nome_canal

    # 2. Teste via Fábrica de Fontes
    config_global = ConfiguracaoGlobal(
        projeto=ConfiguracaoProjeto(nome="teste_fonte", idioma="pt_BR"),
        coleta=config_coleta,
        processamento=ConfiguracaoProcessamento(
            reducao=ConfiguracaoReducao(ativa=False, tecnica=TecnicaReducao.PCA, componentes=2),
            tecnicas=ConfiguracaoTecnicas(
                kmeans_ativo=True,
                kmeans_parametros=ParametrosKMeans(n_clusters=2, random_state=42, n_init=2, init=InicializacaoKMeans.KMEANS_PLUS_PLUS),
                dbscan_ativo=False,
                dbscan_parametros=ParametrosDBSCAN(eps=0.5, min_samples=2, metric=MetricaDistancia.EUCLIDEAN, algorithm=AlgoritmoVizinhos.AUTO),
                hdbscan_ativo=False,
                hdbscan_parametros=ParametrosHDBSCAN(min_cluster_size=2, min_samples=1, metric=MetricaDistancia.EUCLIDEAN, cluster_selection_method=MetodoSelecaoCluster.EOM),
            ),
        ),
        topicos=ConfiguracaoTopicos(),
        tendencias=ConfiguracaoTendencias(),
        persistencia=ConfiguracaoPersistencia(
            tipo=TipoPersistencia.S3,
            bucket="teste",
            prefixo_bronze="b",
            prefixo_prata="p",
            prefixo_ouro="o",
            endpoint_env="E",
            access_key_env="A",
            secret_key_env="S",
        ),
        mlflow=ConfiguracaoMLflow(tracking_uri_env="U", serving_url_env="S"),
        api=ConfiguracaoAPI(porta=8000, tempo_limite_segundos=10.0),
        observabilidade=ConfiguracaoObservabilidade(prometheus=True, grafana=True, labels_alta_cardinalidade=False),
    )

    fonte_fab = FabricaFontesDados.criar_extrator(config_global)
    assert isinstance(fonte_fab, ExtratorArquivoLocal)

