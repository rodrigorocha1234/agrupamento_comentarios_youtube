"""Orquestrador de compatibilidade para coleta incremental da Steam."""

from app.contratos.fonte_dados import ProtocoloFonteDados
from app.contratos.repositorio import ProtocoloRepositorioLakehouse
from app.contratos.tipos_dados import DicionarioJson
from app.ingestao_fontes.coletor_dados import ColetorDados


class ColetorSteam(ColetorDados):
    """Orquestrador da coleta incremental de avaliações da Steam."""

    def __init__(
        self,
        fonte: ProtocoloFonteDados,
        repositorio: ProtocoloRepositorioLakehouse,
        campo_deduplicacao: str = "recommendationid",
    ) -> None:
        super().__init__(
            fonte=fonte,
            repositorio=repositorio,
            campo_deduplicacao=campo_deduplicacao,
        )

    def coletar_jogo(
        self,
        appid: int,
        cursor_inicial: str = "*",
        limite_total: int = 1000,
        tamanho_lote: int = 100,
        pausa_segundos: float = 0.2,
    ) -> DicionarioJson:
        """Método de conveniência para coletar avaliações de um jogo específico da Steam."""
        return self.executar_coleta(
            identificador_origem=appid,
            marcador_inicial=cursor_inicial,
            limite_total_registros=limite_total,
            tamanho_lote=tamanho_lote,
            pausa_entre_lotes_segundos=pausa_segundos,
        )
