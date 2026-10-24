"""Escritor imutável de payloads brutos em JSON para a camada Bronze do Data Lake."""

from typing import final

from app.dominio_contratos.protocolos_datalake import ArmazenamentoLake


@final
class EscritorCamadaBronze:
    """Persiste arquivos JSON imutáveis com particionamento estruturado."""

    def __init__(
        self,
        armazenamento: ArmazenamentoLake,
        prefixo_base: str = "bronze/steam/reviews",
    ) -> None:
        self._armazenamento = armazenamento
        self._prefixo = prefixo_base.strip("/")

    def construir_caminho_particao(
        self, appid: int, data_coleta: str, id_execucao: str, numero_pagina: int
    ) -> str:
        """Gera o caminho hierárquico particionado para a página."""
        return (
            f"{self._prefixo}/appid={appid}/data_coleta={data_coleta}/"
            f"execucao={id_execucao}/pagina_{numero_pagina:04d}.json"
        )

    def salvar_pagina_bruta(
        self,
        appid: int,
        data_coleta: str,
        id_execucao: str,
        numero_pagina: int,
        conteudo_json: str,
    ) -> str:
        """Grava a página no bucket se ainda não existir, preservando imutabilidade."""
        caminho = self.construir_caminho_particao(
            appid, data_coleta, id_execucao, numero_pagina
        )
        if not self._armazenamento.verificar_existencia(caminho):
            self._armazenamento.gravar_texto(caminho, conteudo_json)
        return caminho
