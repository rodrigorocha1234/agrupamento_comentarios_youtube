"""Rotulagem semântica pós-treinamento por regras declarativas sem alterar clusters."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import final

import numpy as np
import pandas as pd

from app.dominio_contratos.modelos_dados import TipoDadoJson, TipoValorEscalar
from app.regras_negocio.especificacao_negocio import (
    EspecificacaoCompostaAnd,
    EspecificacaoCompostaOr,
    EspecificacaoCondicao,
    EspecificacaoNegocio,
)


def _extrair_array_float(serie: pd.Series | pd.DataFrame | Sequence[float] | None) -> np.ndarray:
    """Extrai array unidimensional de floats finitos ignorando NaNs."""
    if not isinstance(serie, pd.Series):
        return np.empty(0, dtype=np.float64)
    arr_puro = np.asarray(serie.to_numpy(), dtype=np.float64)
    return arr_puro[np.isfinite(arr_puro)]


@dataclass(frozen=True, slots=True)
class RegraDeclarativaNegocio:
    """Definição de uma regra de negócio carregada de configuração."""

    identificador: str
    rotulo: str
    especificacao: EspecificacaoNegocio


@final
class RotuladorClusters:
    """Aplica regras de negócio para rotular clusters de forma não destrutiva."""

    def __init__(self, regras: Sequence[RegraDeclarativaNegocio] | None = None) -> None:
        self._regras = list(regras or [])

    @classmethod
    def de_configuracao(
        cls, definicoes_regras: Sequence[Mapping[str, TipoDadoJson]]
    ) -> "RotuladorClusters":
        """Instancia o rotulador a partir da estrutura declarativa em YAML."""
        regras_compiladas: list[RegraDeclarativaNegocio] = []

        for reg in definicoes_regras:
            identificador = str(reg.get("identificador", "regra_anonima"))
            rotulo = str(reg.get("rotulo", identificador))
            combinacao = str(reg.get("combinacao", "and")).lower()
            condicoes_brutas = reg.get("condicoes")

            if not isinstance(condicoes_brutas, (list, tuple)):
                continue

            sub_especificacoes: list[EspecificacaoNegocio] = []
            for cond in condicoes_brutas:
                if not isinstance(cond, Mapping):
                    continue
                metrica = str(cond.get("metrica", ""))
                operador = str(cond.get("operador", "igual"))
                valor = cond.get("valor")
                sub_especificacoes.append(
                    EspecificacaoCondicao(metrica, operador, valor)
                )

            if combinacao == "or":
                esp_final: EspecificacaoNegocio = EspecificacaoCompostaOr(
                    sub_especificacoes
                )
            else:
                esp_final = EspecificacaoCompostaAnd(sub_especificacoes)

            regras_compiladas.append(
                RegraDeclarativaNegocio(
                    identificador=identificador,
                    rotulo=rotulo,
                    especificacao=esp_final,
                )
            )

        return cls(regras_compiladas)

    def rotular_clusters(
        self,
        dados_gold: pd.DataFrame,
        coluna_cluster: str = "cluster_id",
        rotulo_padrao: str = "padrao_nao_classificado",
    ) -> tuple[pd.DataFrame, dict[int, str]]:
        """Avalia estatísticas agregadas por cluster e mapeia rótulos semânticos."""
        resultado = dados_gold.copy()

        if coluna_cluster not in resultado.columns:
            resultado["rotulo_negocio"] = rotulo_padrao
            return resultado, {}

        mapa_rotulos: dict[int, str] = {}
        clusters_unicos = resultado[coluna_cluster].unique()

        for c_id in clusters_unicos:
            cluster_int = int(c_id)
            if cluster_int == -1:
                mapa_rotulos[cluster_int] = "ruido_estatistico"
                continue

            sub_df = pd.DataFrame(
                resultado.loc[resultado[coluna_cluster] == cluster_int]
            )
            contexto = self._extrair_contexto_cluster(sub_df)

            rotulo_atribuido = rotulo_padrao
            for regra in self._regras:
                if regra.especificacao.satisfeita_por(contexto):
                    rotulo_atribuido = regra.rotulo
                    break

            mapa_rotulos[cluster_int] = rotulo_atribuido

        # Adiciona a coluna descritiva sem alterar a coluna cluster_id original
        def _obter_rotulo(cid: str | float | None) -> str:
            try:
                return mapa_rotulos.get(int(str(cid)), rotulo_padrao)
            except (ValueError, TypeError):
                return rotulo_padrao

        resultado["rotulo_negocio"] = resultado[coluna_cluster].map(_obter_rotulo)

        return resultado, mapa_rotulos

    def _extrair_contexto_cluster(self, sub_df: pd.DataFrame) -> dict[str, TipoValorEscalar]:
        """Calcula métricas agregadas descritivas de um cluster para avaliação de regras."""
        contexto: dict[str, TipoValorEscalar] = {
            "total_membros": len(sub_df),
        }

        # Horas jogadas
        if "horas_jogadas_total" in sub_df.columns:
            arr_horas = _extrair_array_float(sub_df["horas_jogadas_total"])
            contexto["mediana_horas_jogadas"] = (
                float(np.median(arr_horas)) if len(arr_horas) > 0 else 0.0
            )
            contexto["media_horas_jogadas"] = (
                float(np.mean(arr_horas)) if len(arr_horas) > 0 else 0.0
            )

        # Percentual de reviews negativas
        if "voted_up" in sub_df.columns:
            arr_voto = np.asarray(sub_df["voted_up"].to_numpy(), dtype=np.bool_)
            total = len(arr_voto)
            positivas = int(np.sum(arr_voto))
            negativas = total - positivas
            contexto["percentual_reviews_negativas"] = (
                (float(negativas) / float(total) * 100.0) if total > 0 else 0.0
            )
            contexto["percentual_reviews_positivas"] = (
                (float(positivas) / float(total) * 100.0) if total > 0 else 0.0
            )

        # Engajamento por votos úteis
        if "votes_up" in sub_df.columns:
            arr_votos = _extrair_array_float(sub_df["votes_up"])
            contexto["mediana_votos_up"] = (
                float(np.median(arr_votos)) if len(arr_votos) > 0 else 0.0
            )

        return contexto
