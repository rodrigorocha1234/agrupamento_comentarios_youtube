"""Fábrica de transformadores de pré-processamento de ML baseada em scikit-learn."""

from collections.abc import Callable
from typing import Final

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    FunctionTransformer,
    MaxAbsScaler,
    MinMaxScaler,
    PowerTransformer,
    QuantileTransformer,
    RobustScaler,
    StandardScaler,
)

from app.conf_yaml import ConfigPreprocessamentoInfo
from app.excecoes import ErroPreprocessamento


def _transformar_log1p_seguro(matriz: np.ndarray) -> np.ndarray:
    """Aplica log1p com corte seguro em 0.0 para evitar NaNs em números negativos."""
    valores_limpos = np.maximum(matriz, 0.0)
    return np.log1p(valores_limpos)


_MAPA_TRANSFORMACOES_NUMERICAS: Final[dict[str, Callable[[], BaseEstimator | TransformerMixin]]] = {
    "log1p": lambda: FunctionTransformer(func=_transformar_log1p_seguro, validate=False),
    "power": lambda: PowerTransformer(method="yeo-johnson"),
    "quantile": lambda: QuantileTransformer(output_distribution="normal", random_state=42),
}

_MAPA_ESCALONADORES: Final[dict[str, type[BaseEstimator | TransformerMixin]]] = {
    "standard": StandardScaler,
    "minmax": MinMaxScaler,
    "robust": RobustScaler,
    "maxabs": MaxAbsScaler,
}

_MAPA_REDUCAO_DIMENSIONAL: Final[dict[str, type[PCA | TruncatedSVD]]] = {
    "pca": PCA,
    "truncated_svd": TruncatedSVD,
}


class FabricaTransformadores:
    """Monta pipelines compostos do scikit-learn baseados nas especificações YAML."""

    @staticmethod
    def criar_pipeline(config: ConfigPreprocessamentoInfo) -> Pipeline:
        """Constrói uma esteira scikit-learn encadeando imputação, transformação, escala e redução.

        Args:
            config: Modelo de configuração validado de preprocessamento.yaml.

        Retorna:
            Pipeline ajustável via fit/transform.
        """
        if not config.habilitado:
            # Pipeline identidade que retorna os dados originais
            return Pipeline(steps=[("identidade", FunctionTransformer(func=None, validate=False))])

        passos: list[tuple[str, BaseEstimator | TransformerMixin]] = []

        # 1. Imputação de Valores Ausentes
        match config.valores_ausentes.estrategia:
            case "constant":
                passos.append(
                    (
                        "imputer",
                        SimpleImputer(
                            strategy="constant",
                            fill_value=config.valores_ausentes.valor_constante,
                        ),
                    )
                )
            case "mean" | "median" | "most_frequent" as estrat:
                passos.append(("imputer", SimpleImputer(strategy=estrat)))
            case estrat_invalida:
                raise ErroPreprocessamento(
                    f"Estratégia de imputação '{estrat_invalida}' não suportada. "
                    "Opções válidas: 'mean', 'median', 'most_frequent', 'constant'."
                )

        # 2. Transformações Numéricas Não Lineares (opcional)
        if config.transformacoes_numericas.habilitado:
            match config.transformacoes_numericas.estrategia:
                case "log1p" | "power" | "quantile" as estrat:
                    passos.append(
                        (f"transformacao_{estrat}", _MAPA_TRANSFORMACOES_NUMERICAS[estrat]())
                    )

        # 3. Escalonamento e Normalização
        match str(config.escalonamento.estrategia):
            case "none":
                pass
            case "standard" | "minmax" | "robust" | "maxabs" as estrat:
                passos.append(("escalonamento", _MAPA_ESCALONADORES[estrat]()))
            case estrat_invalida:
                raise ErroPreprocessamento(
                    f"Estratégia de escalonamento '{estrat_invalida}' não suportada. "
                    "Opções válidas: 'standard', 'minmax', 'robust', 'maxabs', 'none'."
                )

        # 4. Redução de Dimensionalidade (opcional)
        if config.reducao_dimensional.habilitado:
            match config.reducao_dimensional.estrategia:
                case "pca" | "truncated_svd" as estrat:
                    passos.append(
                        (
                            "reducao_dimensional",
                            _MAPA_REDUCAO_DIMENSIONAL[estrat](
                                n_components=config.reducao_dimensional.componentes,
                                random_state=42,
                            ),
                        )
                    )

        return Pipeline(steps=passos)
