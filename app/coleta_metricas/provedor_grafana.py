"""Implementação desacoplada do provedor de visualização e dashboards Grafana."""

from __future__ import annotations

import json
from typing import Any
import urllib.error
import urllib.request

from app.coleta_metricas.protocolo_visualizacao import ProtocoloProvedorVisualizacao
from app.configuracao_geral.tipos_enumerados import TipoProvedorVisualizacao


class ProvedorVisualizacaoGrafana(ProtocoloProvedorVisualizacao):
    """Encapsula toda a integração, mapeamento de dashboards e verificações específicas do Grafana."""

    DASHBOARDS_CONHECIDOS: dict[str, dict[str, str]] = {
        "yt-pipe-operacional": {
            "uid": "yt-pipe-operacional",
            "slug": "pipeline-operacional-and-ingestao-youtube",
            "titulo": "Pipeline Operacional & Ingestão",
            "descricao": "Monitoramento de jobs diários, taxas de erro e duração de execução.",
        },
        "yt-datalake-lakehouse": {
            "uid": "yt-datalake-lakehouse",
            "slug": "data-lakehouse-and-armazenamento-s3-rustfs",
            "titulo": "Data Lakehouse & Armazenamento S3 RustFS",
            "descricao": "Volumetria e contagem de objetos nas camadas Bronze, Prata e Ouro.",
        },
        "yt-api-fastapi": {
            "uid": "yt-api-fastapi",
            "slug": "api-fastapi-and-serving-operacional",
            "titulo": "API FastAPI & Serving Operacional",
            "descricao": "Vazão de requisições HTTP, latência p95/p99 e status codes.",
        },
        "yt-clusters-modelos": {
            "uid": "yt-clusters-modelos",
            "slug": "qualidade-de-agrupamento-and-modelos-de-ml",
            "titulo": "Qualidade de Agrupamento & Modelos de ML",
            "descricao": "Scores de silhueta, Davies-Bouldin, Calinski-Harabasz e proporção de ruído.",
        },
    }

    def __init__(self, url_base: str = "http://localhost:3000") -> None:
        self._url_base = url_base.rstrip("/")

    @property
    def tipo_provedor(self) -> TipoProvedorVisualizacao:
        """Identificador canônico do Grafana."""
        return TipoProvedorVisualizacao.GRAFANA

    @property
    def url_base(self) -> str:
        """URL base de conexão com o Grafana."""
        return self._url_base

    def verificar_disponibilidade(self, timeout_segundos: float = 2.0) -> bool:
        """Consulta a API interna de healthcheck do Grafana (/api/health)."""
        url = f"{self._url_base}/api/health"
        try:
            requisicao = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": "PipelineObservabilidade/1.0"},
            )
            with urllib.request.urlopen(requisicao, timeout=timeout_segundos) as resposta:
                if resposta.status == 200:
                    corpo = json.loads(resposta.read().decode("utf-8"))
                    return corpo.get("database") in ("ok", "healthy") or corpo.get("version") is not None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return False
        return False

    def obter_url_dashboard(self, identificador: str) -> str:
        """Gera a URL navegável do dashboard a partir do UID ou alias."""
        meta = self.DASHBOARDS_CONHECIDOS.get(identificador)
        if meta is not None:
            return f"{self._url_base}/d/{meta['uid']}/{meta['slug']}"
        return f"{self._url_base}/d/{identificador}"

    def listar_dashboards(self) -> list[dict[str, Any]]:
        """Lista os dashboards conhecidos e provisionados no Grafana."""
        resultado: list[dict[str, Any]] = []
        for uid, dados in self.DASHBOARDS_CONHECIDOS.items():
            resultado.append(
                {
                    "uid": uid,
                    "slug": dados["slug"],
                    "titulo": dados["titulo"],
                    "descricao": dados["descricao"],
                    "url": self.obter_url_dashboard(uid),
                }
            )
        return resultado

    def obter_metadados_painel(self, identificador: str) -> dict[str, Any]:
        """Obtém detalhes do painel solicitado."""
        meta = self.DASHBOARDS_CONHECIDOS.get(identificador)
        if meta is None:
            return {
                "uid": identificador,
                "url": f"{self._url_base}/d/{identificador}",
                "status": "personalizado_ou_desconhecido",
            }
        return {
            "uid": meta["uid"],
            "slug": meta["slug"],
            "titulo": meta["titulo"],
            "descricao": meta["descricao"],
            "url": self.obter_url_dashboard(meta["uid"]),
            "status": "provisionado",
        }
