"""Fábrica de estratégias de clusterização configuradas."""

from typing import Protocol
import numpy as np
from scipy.sparse import csr_matrix

from app.agrupamento_modelos.agrupador_dbscan import AgrupadorDBSCAN
from app.agrupamento_modelos.agrupador_hdbscan import AgrupadorHDBSCAN
from app.agrupamento_modelos.agrupador_kmeans import AgrupadorKMeans
from app.agrupamento_modelos.avaliador_qualidade import MetricasAgrupamento
from app.configuracao_geral.modelos_configuracao import (
    ConfiguracaoProcessamento,
)
from app.configuracao_geral.tipos_enumerados import TecnicaCluster


class ProtocoloAgrupador(Protocol):
    """Protocolo estrutural para estratégias desacopladas de clustering."""

    def ajustar_e_agrupar(
        self,
        matriz: csr_matrix | np.ndarray,
    ) -> tuple[list[int], MetricasAgrupamento]: ...


class FabricaAgrupadores:
    """Instancia os algoritmos de agrupamento conforme configuração YAML."""

    @staticmethod
    def criar_agrupador(
        nome_tecnica: TecnicaCluster | str,
        config: ConfiguracaoProcessamento,
    ) -> ProtocoloAgrupador:
        """Cria e devolve o agrupador correspondente à técnica informada."""
        nome_limpo = str(nome_tecnica).strip().lower()

        if nome_limpo == TecnicaCluster.KMEANS:
            params_km = config.tecnicas.kmeans_parametros
            return AgrupadorKMeans(
                n_clusters=params_km.n_clusters,
                random_state=params_km.random_state,
                n_init=params_km.n_init,
                init=params_km.init,
                k_automatico=params_km.k_automatico,
                k_min=params_km.k_min,
                k_max=params_km.k_max,
                max_iter=params_km.max_iter,
            )

        if nome_limpo == TecnicaCluster.DBSCAN:
            params_db = config.tecnicas.dbscan_parametros
            return AgrupadorDBSCAN(
                eps=params_db.eps,
                min_samples=params_db.min_samples,
                metric=params_db.metric,
                algorithm=params_db.algorithm,
            )

        if nome_limpo == TecnicaCluster.HDBSCAN:
            params_hdb = config.tecnicas.hdbscan_parametros
            return AgrupadorHDBSCAN(
                min_cluster_size=params_hdb.min_cluster_size,
                min_samples=params_hdb.min_samples,
                metric=params_hdb.metric,
                cluster_selection_method=params_hdb.cluster_selection_method,
            )

        raise ValueError(f"Técnica de clusterização desconhecida: '{nome_tecnica}'")
