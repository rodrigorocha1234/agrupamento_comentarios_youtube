"""Módulo de sumarização diagnóstica e análise de perfis de clusters."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from app.conf_yaml import ConfigAnalisesInfo
    from app.regras_negocio.avaliador_regras import AvaliadorRegrasNegocio

ROTULO_RUIDO: Final[str] = "Ruído / Outlier"


@dataclass(frozen=True)
class PerfilCluster:
    """Consolida as características estatísticas de um cluster específico."""

    id_cluster: int
    nome_rotulo: str
    quantidade_amostras: int
    proporcao_amostras: float
    medias_atributos: dict[str, float]
    medianas_atributos: dict[str, float]
    distancia_media_centroide: float | None = None
    rotulo_negocio: str | None = None
    alerta_negocio: bool = False
    prioridade_negocio: str | None = None
    metricas_personalizadas: dict[str, float] = field(default_factory=dict)

    def __getattr__(self, item: str) -> float | None:
        """Permite acesso dinâmico e transparente aos atributos configurados via YAML."""
        if item in self.metricas_personalizadas:
            return self.metricas_personalizadas[item]
        return None


@dataclass(frozen=True)
class ResumoAnaliseClusters:
    """Relatório estruturado de perfis de todos os agrupamentos gerados."""

    perfis: list[PerfilCluster]
    total_amostras: int
    quantidade_clusters_validos: int
    quantidade_ruido: int
    proporcao_ruido: float
    atributos_analisados: list[str]


class AnalisadorClusters:
    """Calcula estatísticas descritivas, perfis agregados e isolamento de ruído."""

    @classmethod
    def _obter_config_analises_padrao(cls) -> "ConfigAnalisesInfo | None":
        """Carrega a configuração de análises padrão a partir do YAML do projeto se existir."""
        try:
            from app.conf_yaml import ConfigAnalisesInfo

            return ConfigAnalisesInfo.carregar_de_arquivo()
        except (OSError, ValueError, TypeError):
            return None

    @classmethod
    def gerar_resumo_estatistico(
        cls,
        matriz_treino: pd.DataFrame | np.ndarray,
        rotulos: list[int],
        metadados: pd.DataFrame | None = None,
        centroides: np.ndarray | None = None,
        nomes_colunas_matriz: list[str] | None = None,
        avaliador_regras: "AvaliadorRegrasNegocio | None" = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> ResumoAnaliseClusters:
        """Produz o sumário descritivo por cluster cruzando atributos com metadados configurados."""
        total_amostras = len(rotulos)
        if total_amostras == 0:
            return ResumoAnaliseClusters(
                perfis=[],
                total_amostras=0,
                quantidade_clusters_validos=0,
                quantidade_ruido=0,
                proporcao_ruido=0.0,
                atributos_analisados=[],
            )

        cfg_analises: ConfigAnalisesInfo | None = config_analises or cls._obter_config_analises_padrao()

        if isinstance(matriz_treino, pd.DataFrame):
            colunas_atributos = list(matriz_treino.columns)
            matriz_np = np.asarray(matriz_treino.to_numpy(dtype=np.float64), dtype=np.float64)
        else:
            matriz_np = np.asarray(matriz_treino, dtype=np.float64)
            colunas_atributos = (
                nomes_colunas_matriz
                if nomes_colunas_matriz is not None and len(nomes_colunas_matriz) == matriz_np.shape[1]
                else [f"attr_{i}" for i in range(matriz_np.shape[1])]
            )

        rotulos_unicos = sorted(set(rotulos))
        clusters_validos = [r for r in rotulos_unicos if r != -1]
        qtd_ruido = rotulos.count(-1)
        prop_ruido = float(qtd_ruido / total_amostras)

        # Distâncias aos centroides se presentes
        distancias: np.ndarray | None = None
        if centroides is not None and len(centroides) > 0 and len(clusters_validos) > 0:
            distancias = np.zeros(total_amostras, dtype=np.float64)
            for idx, r in enumerate(rotulos):
                if 0 <= r < len(centroides):
                    ponto = matriz_np[idx]
                    centro = centroides[r]
                    distancias[idx] = float(np.linalg.norm(ponto - centro))
                else:
                    distancias[idx] = np.nan

        perfis: list[PerfilCluster] = []

        for r in rotulos_unicos:
            mascara = [i for i, val in enumerate(rotulos) if val == r]
            qtd = len(mascara)
            prop = float(qtd / total_amostras)
            nome = ROTULO_RUIDO if r == -1 else f"Cluster {r}"

            subset_matriz = matriz_np[mascara]

            medias: dict[str, float] = {}
            medianas: dict[str, float] = {}
            for col_idx, nome_col in enumerate(colunas_atributos):
                medias[nome_col] = float(np.mean(subset_matriz[:, col_idx]))
                medianas[nome_col] = float(np.median(subset_matriz[:, col_idx]))

            metricas_personalizadas: dict[str, float] = {}

            if metadados is not None and not metadados.empty and cfg_analises is not None:
                subset_meta = metadados.iloc[mascara]
                for cfg_m in cfg_analises.metricas_resumo:
                    if cfg_m.coluna in subset_meta.columns:
                        col_vals = subset_meta[cfg_m.coluna]
                        divisor = cfg_m.divisor if cfg_m.divisor != 0.0 else 1.0
                        val_calc: float
                        if cfg_m.operacao in ("media", "proporcao"):
                            val_calc = float(col_vals.astype(float).mean() / divisor)
                        elif cfg_m.operacao == "soma":
                            val_calc = float(col_vals.astype(float).sum() / divisor)
                        elif cfg_m.operacao == "mediana":
                            val_calc = float(col_vals.astype(float).median() / divisor)
                        else:
                            val_calc = float(col_vals.astype(float).mean() / divisor)

                        metricas_personalizadas[cfg_m.nome] = val_calc

            dist_media: float | None = None
            if distancias is not None and r != -1:
                dist_subset = distancias[mascara]
                dist_validas = dist_subset[~np.isnan(dist_subset)]
                if len(dist_validas) > 0:
                    dist_media = float(np.mean(dist_validas))

            perfil_obj = PerfilCluster(
                id_cluster=r,
                nome_rotulo=nome,
                quantidade_amostras=qtd,
                proporcao_amostras=prop,
                medias_atributos=medias,
                medianas_atributos=medianas,
                distancia_media_centroide=dist_media,
                metricas_personalizadas=metricas_personalizadas,
            )
            if avaliador_regras is not None:
                perfil_obj = avaliador_regras.aplicar_regras_perfil(perfil_obj)

            perfis.append(perfil_obj)

        return ResumoAnaliseClusters(
            perfis=perfis,
            total_amostras=total_amostras,
            quantidade_clusters_validos=len(clusters_validos),
            quantidade_ruido=qtd_ruido,
            proporcao_ruido=prop_ruido,
            atributos_analisados=colunas_atributos,
        )

    @classmethod
    def extrair_amostras_reviews_por_cluster(
        cls,
        metadados: pd.DataFrame,
        rotulos: list[int],
        amostras_por_cluster: int = 5,
        colunas_exibicao: list[str] | None = None,
        config_analises: "ConfigAnalisesInfo | None" = None,
    ) -> dict[int, list[dict[str, str | int | float | bool]]]:
        """Extrai exemplos de dados originais por cluster usando colunas configuradas no YAML."""
        if metadados.empty or len(rotulos) != len(metadados):
            return {}

        cfg_analises: ConfigAnalisesInfo | None = config_analises or cls._obter_config_analises_padrao()

        # Determina as colunas a extrair: parâmetro explícito, YAML analises.yaml ou colunas do DataFrame
        colunas_alvo: list[str]
        if colunas_exibicao is not None and len(colunas_exibicao) > 0:
            colunas_alvo = colunas_exibicao
        elif cfg_analises is not None and cfg_analises.amostras.colunas:
            colunas_alvo = cfg_analises.amostras.colunas
        else:
            colunas_alvo = list(metadados.columns)

        df_aux = metadados.copy()
        df_aux["_cluster_rotulo"] = rotulos

        resultado: dict[int, list[dict[str, str | int | float | bool]]] = {}
        for r in sorted(set(rotulos)):
            subset = df_aux[df_aux["_cluster_rotulo"] == r]
            amostra = subset.head(amostras_por_cluster)

            lista_registros: list[dict[str, str | int | float | bool]] = []
            for _, row in amostra.iterrows():
                registro: dict[str, str | int | float | bool] = {}
                for col in colunas_alvo:
                    if col in row:
                        val = row[col]
                        if bool(pd.isna(val)):
                            registro[col] = ""
                        elif isinstance(val, (bool, int, float, str)):
                            registro[col] = val
                        else:
                            registro[col] = str(val)
                lista_registros.append(registro)

            resultado[r] = lista_registros

        return resultado
