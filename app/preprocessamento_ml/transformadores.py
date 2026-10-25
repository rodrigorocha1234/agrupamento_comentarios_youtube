"""Fábrica de transformadores de pré-processamento de ML baseada em scikit-learn."""

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
        estrategia_imputer = config.valores_ausentes.estrategia
        if estrategia_imputer == "constant":
            passos.append(
                (
                    "imputer",
                    SimpleImputer(
                        strategy="constant",
                        fill_value=config.valores_ausentes.valor_constante,
                    ),
                )
            )
        elif estrategia_imputer in ("mean", "median", "most_frequent"):
            passos.append(
                (
                    "imputer",
                    SimpleImputer(strategy=estrategia_imputer),
                )
            )
        else:
            raise ErroPreprocessamento(
                f"Estratégia de imputação '{estrategia_imputer}' não suportada. "
                "Opções válidas: 'mean', 'median', 'most_frequent', 'constant'."
            )

        # 2. Transformações Numéricas Não Lineares (opcional)
        if config.transformacoes_numericas.habilitado:
            estrat_num = config.transformacoes_numericas.estrategia
            if estrat_num == "log1p":
                passos.append(
                    (
                        "transformacao_log1p",
                        FunctionTransformer(func=_transformar_log1p_seguro, validate=False),
                    )
                )
            elif estrat_num == "power":
                passos.append(
                    (
                        "transformacao_power",
                        PowerTransformer(method="yeo-johnson"),
                    )
                )
            elif estrat_num == "quantile":
                passos.append(
                    (
                        "transformacao_quantile",
                        QuantileTransformer(output_distribution="normal", random_state=42),
                    )
                )

        # 3. Escalonamento e Normalização
        estrat_escala = config.escalonamento.estrategia
        if estrat_escala == "standard":
            passos.append(("escalonamento", StandardScaler()))
        elif estrat_escala == "minmax":
            passos.append(("escalonamento", MinMaxScaler()))
        elif estrat_escala == "robust":
            passos.append(("escalonamento", RobustScaler()))
        elif estrat_escala == "maxabs":
            passos.append(("escalonamento", MaxAbsScaler()))
        elif estrat_escala == "none":
            pass
        else:
            raise ErroPreprocessamento(
                f"Estratégia de escalonamento '{estrat_escala}' não suportada. "
                "Opções válidas: 'standard', 'minmax', 'robust', 'maxabs', 'none'."
            )

        # 4. Redução de Dimensionalidade (opcional)
        if config.reducao_dimensional.habilitado:
            estrat_red = config.reducao_dimensional.estrategia
            n_comp = config.reducao_dimensional.componentes
            if estrat_red == "pca":
                passos.append(("reducao_dimensional", PCA(n_components=n_comp, random_state=42)))
            elif estrat_red == "truncated_svd":
                passos.append(
                    ("reducao_dimensional", TruncatedSVD(n_components=n_comp, random_state=42))
                )

        return Pipeline(steps=passos)
