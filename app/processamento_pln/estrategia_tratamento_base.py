"""Protocolo base (GoF Strategy) para tratamento e vetorização de texto."""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class ProtocoloTratamentoTexto(Protocol):
    """Contrato base para estratégias de pré-processamento e vetorização de linguagem natural."""

    def processar_textos(self, textos: Sequence[str]) -> pd.DataFrame:
        """Processa e transforma uma coleção de textos em uma matriz numérica tabular.

        Args:
            textos: Sequência de textos brutos (ex: avaliações Steam).

        Retorna:
            DataFrame contendo as variáveis numéricas vetorizadas e indexado sequencialmente.
        """
        ...
