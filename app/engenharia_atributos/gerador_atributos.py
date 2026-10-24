"""Geração vetorizada de atributos derivados para clustering a partir de dados da Steam."""

from datetime import UTC, datetime
from typing import final

import numpy as np
import pandas as pd


@final
class GeradorAtributosDerivados:
    """Calcula variáveis numéricas analíticas a partir dos campos brutos da review."""

    def calcular_atributos(
        self,
        dados: pd.DataFrame,
        timestamp_referencia: int | None = None,
    ) -> pd.DataFrame:
        """Adiciona variáveis derivadas vetorizadas preservando colunas originais."""
        if dados.empty:
            return dados.copy()

        resultado = dados.copy()
        ref = timestamp_referencia or int(datetime.now(UTC).timestamp())

        # Horas até a publicação da avaliação
        if "playtime_at_review" in resultado.columns:
            resultado["horas_ate_review"] = resultado["playtime_at_review"] / 60.0

        # Dias desde a última atividade até o momento de referência da coleta
        if "last_played" in resultado.columns:
            delta_segundos = np.maximum(ref - resultado["last_played"].to_numpy(), 0.0)
            resultado["dias_desde_ultima_atividade"] = delta_segundos / 86400.0

        # Proporção de jogo recente (últimas 2 semanas vs tempo total)
        if (
            "playtime_last_two_weeks" in resultado.columns
            and "playtime_forever" in resultado.columns
        ):
            tempo_total = resultado["playtime_forever"].to_numpy() + 1.0
            resultado["proporcao_jogo_recente"] = (
                resultado["playtime_last_two_weeks"].to_numpy() / tempo_total
            )

        # Horas jogadas após a publicação da avaliação
        if (
            "playtime_forever" in resultado.columns
            and "playtime_at_review" in resultado.columns
        ):
            horas_posteriores = np.maximum(
                resultado["playtime_forever"].to_numpy()
                - resultado["playtime_at_review"].to_numpy(),
                0.0,
            )
            resultado["horas_apos_review"] = horas_posteriores / 60.0

        return resultado
