from __future__ import annotations

import os
from typing import TYPE_CHECKING

from app.coleta_youtube.cliente_youtube import ClienteYouTube
from app.coleta_youtube.extrator_arquivo_local import ExtratorArquivoLocal
from app.coleta_youtube.extrator_comentarios import ExtratorComentarios
from app.configuracao_geral.modelos_configuracao import ConfiguracaoGlobal
from app.configuracao_geral.tipos_enumerados import TipoFonteDados

if TYPE_CHECKING:
    from app.orquestracao_pipeline.protocolos_ciclo import ProtocoloExtratorComentarios


class FabricaFontesDados:
    """Instancia polimorficamente a fonte de dados conforme a configuração declarativa."""

    @staticmethod
    def criar_extrator(
        config: ConfiguracaoGlobal,
        cliente_youtube: ClienteYouTube | None = None,
    ) -> ProtocoloExtratorComentarios:
        """Cria o extrator correspondente ao tipo de fonte configurado."""
        fonte = config.coleta.fonte

        if fonte in [
            TipoFonteDados.CSV,
            TipoFonteDados.PARQUET,
            TipoFonteDados.JSONL,
            TipoFonteDados.LOCAL,
        ]:
            return ExtratorArquivoLocal(config.coleta)

        # Padrão: YouTube
        if cliente_youtube is not None:
            return ExtratorComentarios(cliente_youtube=cliente_youtube)

        chave_api = os.getenv(config.coleta.chave_api_env, "MOCK_KEY_LOCAL")
        cliente = ClienteYouTube(
            chave_api=chave_api,
            tentativas=config.coleta.tentativas,
            atraso_base_segundos=config.coleta.atraso_base_segundos,
        )
        return ExtratorComentarios(cliente_youtube=cliente)

