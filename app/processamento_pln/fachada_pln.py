"""Fachada unificada (GoF Facade) para processamento de linguagem natural."""

from collections.abc import Sequence

import pandas as pd

from app.conf_yaml import ConfigPLNInfo
from app.processamento_pln.adaptador_matriz import AdaptadorMatrizPLN
from app.processamento_pln.fabrica_tratamento_pln import FabricaTratamentoPLN


class FachadaProcessamentoPLN:
    """Fachada unificada para resolução de estratégia, vetorização e adaptação de matriz de PLN."""

    def __init__(self, config: ConfigPLNInfo | None = None) -> None:
        self._config = config or ConfigPLNInfo()
        self._estrategia = FabricaTratamentoPLN.criar_estrategia(self._config)
        self._adaptador = AdaptadorMatrizPLN(self._config.fusao)

    @property
    def habilitado(self) -> bool:
        """Indica se a funcionalidade de PLN está ativa."""
        return self._config.habilitado

    def processar_e_fundir(
        self,
        dados_silver: pd.DataFrame,
        matriz_numerica_treino: pd.DataFrame,
    ) -> pd.DataFrame:
        """Extrai a coluna textual, aplica o tratamento selecionado e adapta a matriz final.

        Args:
            dados_silver: DataFrame original da camada Silver contendo a coluna de texto.
            matriz_numerica_treino: Matriz de atributos numéricos já preparados.

        Retorna:
            Matriz de treino enriquecida ou substituída pelo texto vetorizado.
        """
        if not self._config.habilitado:
            return matriz_numerica_treino

        coluna_texto = self._config.coluna_texto
        textos_brutos: Sequence[str]
        if coluna_texto in dados_silver.columns:
            textos_brutos = [str(v or "") for v in dados_silver[coluna_texto]]
        else:
            textos_brutos = [self._config.substituir_vazios_por] * len(dados_silver)

        df_vetorizado = self._estrategia.processar_textos(textos_brutos)
        return self._adaptador.adaptar_fusao(matriz_numerica_treino, df_vetorizado)
