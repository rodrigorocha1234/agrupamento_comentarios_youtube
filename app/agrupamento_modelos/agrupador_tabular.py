"""Motor agnóstico de agrupamento tabular comparativo para dados numéricos (sem NLP)."""

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar, cast
import numpy as np
from scipy.sparse import csr_matrix

from app.agrupamento_modelos.avaliador_qualidade import MetricasAgrupamento
from app.agrupamento_modelos.fabrica_agrupadores import FabricaAgrupadores
from app.analise_tendencias.estrategias_analise import (
    EstrategiaAnaliseClusters,
    FabricaEstrategiaAnalise,
    ResultadoAnaliseCluster,
)
from app.configuracao_geral.modelos_configuracao import ConfiguracaoProcessamento
from app.representacao_texto.fabrica_representacao import FabricaRepresentacao

TModelo = TypeVar("TModelo")
TMatriz = TypeVar("TMatriz", bound=np.ndarray | csr_matrix)


@dataclass(frozen=True, slots=True)
class ResultadoTecnicaTabular(Generic[TModelo]):
    """Resultado detalhado do agrupamento por uma técnica específica."""

    tecnica: str
    rotulos: list[int]
    metricas: MetricasAgrupamento
    modelo: TModelo | None = None
    analise_clusters: list[ResultadoAnaliseCluster[str]] = field(default_factory=list[ResultadoAnaliseCluster[str]])


@dataclass(frozen=True, slots=True)
class ResultadoAgrupamentoTabular(Generic[TModelo]):
    """Contêiner consolidado com a comparação de todas as técnicas executadas."""

    resultados: dict[str, ResultadoTecnicaTabular[TModelo]]
    n_amostras: int
    n_features: int
    reducao_aplicada: bool


class AgrupadorTabular:
    """Orquestrador agnóstico de agrupamento comparativo para dados numéricos ou tabulares."""

    def __init__(self, config: ConfiguracaoProcessamento) -> None:
        self._config: ConfiguracaoProcessamento = config
        self._estrategia: EstrategiaAnaliseClusters[str] = FabricaEstrategiaAnalise.criar_estrategia(config)

    def agrupar_matriz(
        self,
        matriz: np.ndarray | csr_matrix,
        tecnicas: list[str] | None = None,
        indices_temporais: list[int] | None = None,
    ) -> ResultadoAgrupamentoTabular[Any]:
        """Aplica redução dimensional opcional e executa as técnicas de agrupamento ativas.

        Args:
            matriz: Matriz de features numéricas (N x D).
            tecnicas: Lista opcional de técnicas a executar (ex: ['kmeans', 'dbscan', 'hdbscan']).
                      Se omitido, executa todas as ativas na configuração.
            indices_temporais: Lista opcional de timestamps ou inteiros ordenados para análise temporal.

        Returns:
            ResultadoAgrupamentoTabular com rótulos, métricas e análise estática ou temporal.
        """
        shape = getattr(matriz, "shape", None)
        n_amostras = int(shape[0]) if shape is not None and len(shape) > 0 else 0
        n_features = int(shape[1]) if shape is not None and len(shape) > 1 else 0

        matriz_processada = matriz
        reducao_aplicada = False

        # Redução dimensional opcional (UMAP, PCA ou SVD)
        if self._config.reducao.ativa and n_amostras >= 4:
            redutor = FabricaRepresentacao.criar_redutor_opcional(self._config)
            if redutor is not None:
                matriz_processada = redutor.ajustar_e_reduzir(matriz_processada)
                reducao_aplicada = True

        tecnicas_a_executar = tecnicas or self._obter_tecnicas_ativas()
        resultados: dict[str, ResultadoTecnicaTabular[Any]] = {}

        for nome_tecnica in tecnicas_a_executar:
            agrupador = FabricaAgrupadores.criar_agrupador(nome_tecnica, self._config)
            rotulos, metricas = agrupador.ajustar_e_agrupar(matriz_processada)
            modelo_treinado = getattr(agrupador, "obter_modelo", lambda: None)()

            # Análise pós-agrupamento (Temporal vs Estática via Strategy Pattern)
            analise = self._analisar_rotulos(rotulos, indices_temporais)

            resultados[nome_tecnica] = ResultadoTecnicaTabular(
                tecnica=nome_tecnica,
                rotulos=rotulos,
                metricas=metricas,
                modelo=modelo_treinado,
                analise_clusters=analise,
            )

        return ResultadoAgrupamentoTabular(
            resultados=resultados,
            n_amostras=n_amostras,
            n_features=n_features,
            reducao_aplicada=reducao_aplicada,
        )

    def _analisar_rotulos(
        self,
        rotulos: list[int],
        indices_temporais: list[int] | None = None,
    ) -> list[ResultadoAnaliseCluster[str]]:
        """Calcula distribuição dos clusters aplicando a estratégia (temporal ou estática)."""
        if not rotulos:
            return []

        if self._estrategia.eh_temporal() and indices_temporais and len(indices_temporais) == len(rotulos):
            # Divide na mediana temporal para comparar janela atual com janela anterior
            mediana = int(np.median(indices_temporais))
            contagens_atuais: dict[str, int] = {}
            contagens_anteriores: dict[str, int] = {}

            for r, t in zip(rotulos, indices_temporais):
                nome = f"cluster_{r}" if r != -1 else "ruido"
                if t >= mediana:
                    contagens_atuais[nome] = contagens_atuais.get(nome, 0) + 1
                else:
                    contagens_anteriores[nome] = contagens_anteriores.get(nome, 0) + 1

            return self._estrategia.analisar_grupos(contagens_atuais, contagens_anteriores)

        # Análise estática / cross-sectional pura
        contagens: dict[str, int] = {}
        for r in rotulos:
            nome = f"cluster_{r}" if r != -1 else "ruido"
            contagens[nome] = contagens.get(nome, 0) + 1

        return self._estrategia.analisar_grupos(contagens)

    def agrupar_dataframe(
        self,
        df: Any,
        colunas_features: list[str] | None = None,
        tecnicas: list[str] | None = None,
    ) -> ResultadoAgrupamentoTabular[Any]:
        """Extrai features numéricas de DataFrame (Pandas ou Polars) e executa o agrupamento."""
        # Suporte para Polars
        if hasattr(df, "to_numpy"):
            if colunas_features:
                matriz = cast(np.ndarray, df.select(colunas_features).to_numpy())
            else:
                matriz = cast(np.ndarray, df.to_numpy())
        # Suporte para Pandas
        elif hasattr(df, "values"):
            if colunas_features:
                matriz = cast(np.ndarray, df[colunas_features].values)
            else:
                matriz = cast(np.ndarray, df.values)
        else:
            matriz = np.asarray(df, dtype=np.float64)

        return self.agrupar_matriz(matriz, tecnicas=tecnicas)

    def _obter_tecnicas_ativas(self) -> list[str]:
        """Identifica quais algoritmos de clusterização estão habilitados na configuração."""
        ativas: list[str] = []
        if self._config.tecnicas.kmeans_ativo:
            ativas.append("kmeans")
        if self._config.tecnicas.dbscan_ativo:
            ativas.append("dbscan")
        if self._config.tecnicas.hdbscan_ativo:
            ativas.append("hdbscan")
        return ativas
