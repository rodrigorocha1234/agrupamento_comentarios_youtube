"""Adaptador de matriz (GoF Adapter) para fusão entre variáveis textuais e tabulares."""

import pandas as pd

from app.conf_yaml import ConfigFusaoPLNInfo


class AdaptadorMatrizPLN:
    """Adapta e acopla variáveis vetorizadas de texto à matriz analítica do clustering."""

    def __init__(self, config_fusao: ConfigFusaoPLNInfo | None = None) -> None:
        self._config = config_fusao or ConfigFusaoPLNInfo()

    def adaptar_fusao(
        self,
        df_numerico: pd.DataFrame,
        df_textual: pd.DataFrame,
    ) -> pd.DataFrame:
        """Realiza a fusão de acordo com o modo configurado ('apenas_texto' ou 'concatenar').

        Args:
            df_numerico: DataFrame contendo atributos tabulares originais.
            df_textual: DataFrame gerado pela estratégia de PLN.

        Retorna:
            DataFrame pronto para treinamento com índice alinhado.
        """
        if df_textual.empty:
            return df_numerico

        prefixo = self._config.prefixo_coluna
        df_texto_formatado = df_textual.copy()
        df_texto_formatado.columns = [
            col if col.startswith(prefixo) else f"{prefixo}{col}"
            for col in df_texto_formatado.columns
        ]

        # Alinha índice para garantir concatenação segura
        df_texto_formatado.index = df_numerico.index

        if self._config.modo == "concatenar":
            return pd.concat([df_numerico, df_texto_formatado], axis=1)

        # Modo padrão: apenas texto
        return df_texto_formatado
