"""Despacho de alertas e notificações operacionais sem vazamento de segredos."""

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pipeline_youtube")


class DespachanteAlertas:
    """Emite logs e alertas padronizados para monitoramento operacional."""

    @staticmethod
    def alertar_inicio_etapa(nome_etapa: str) -> None:
        """Registra o início de uma etapa do ciclo diário."""
        logger.info("Iniciando etapa do pipeline: %s", nome_etapa)

    @staticmethod
    def alertar_sucesso_etapa(nome_etapa: str, detalhes: str = "") -> None:
        """Registra a conclusão com sucesso da etapa."""
        logger.info("Etapa concluída com sucesso: %s. %s", nome_etapa, detalhes)

    @staticmethod
    def alertar_falha_etapa(nome_etapa: str, erro: Exception) -> None:
        """Registra falha na etapa sanitizando possíveis segredos."""
        msg = str(erro).replace("AIzaSy", "******")
        logger.error("Falha na etapa %s: %s", nome_etapa, msg)
