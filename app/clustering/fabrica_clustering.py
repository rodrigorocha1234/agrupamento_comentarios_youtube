"""Fábrica (Factory) para resolução e instanciação de motores de clustering."""

from app.clustering.motores_sklearn import MotorDBSCAN, MotorHDBSCAN, MotorKMeans
from app.conf_yaml import ConfigClusteringInfo
from app.contratos.motor_clustering import ProtocoloMotorClustering
from app.excecoes import ErroConfiguracao


class FabricaClustering:
    """Instancia a estratégia concreta de clustering selecionada na configuração YAML."""

    @staticmethod
    def criar(config: ConfigClusteringInfo) -> ProtocoloMotorClustering:
        """Alias ergonômico para criar_motor."""
        return FabricaClustering.criar_motor(config)

    @staticmethod
    def criar_motor(config: ConfigClusteringInfo) -> ProtocoloMotorClustering:
        """Resolve a estratégia de agrupamento (KMeans, DBSCAN, HDBSCAN).

        Args:
            config: Modelo validado do arquivo clustering.yaml.

        Retorna:
            Instância que implementa ProtocoloMotorClustering.

        Raises:
            ErroConfiguracao: Se o algoritmo ou motor solicitado não for suportado.
        """
        motor = config.motor.lower().strip()
        algoritmo = config.algoritmo.lower().strip()

        if motor != "sklearn":
            raise ErroConfiguracao(
                f"Motor de clustering '{motor}' não suportado nesta versão. Motor padrão: 'sklearn'."
            )

        if algoritmo == "kmeans":
            return MotorKMeans(
                parametros=config.algoritmos.kmeans,
                random_state=config.random_state,
            )

        if algoritmo == "dbscan":
            return MotorDBSCAN(
                parametros=config.algoritmos.dbscan,
            )

        if algoritmo == "hdbscan":
            return MotorHDBSCAN(
                parametros=config.algoritmos.hdbscan,
            )

        raise ErroConfiguracao(
            f"Algoritmo de clustering '{algoritmo}' não suportado. "
            "Algoritmos autorizados: 'kmeans', 'dbscan', 'hdbscan'."
        )
