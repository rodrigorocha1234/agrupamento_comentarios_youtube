"""Testes de conformidade estática e polimorfismo estrutural com Protocol, Generic e TypeVar."""

import numpy as np
from sklearn.cluster import KMeans

from app.agrupamento_modelos import (
    AgrupadorDBSCAN,
    AgrupadorHDBSCAN,
    AgrupadorKMeans,
    FabricaAgrupadores,
    ProtocoloAgrupador,
    ResultadoAgrupamentoTabular,
    ResultadoTecnicaTabular,
)
from app.analise_tendencias.estrategias_analise import (
    EstrategiaAnaliseClusters,
    EstrategiaAnaliseEstatica,
    ResultadoAnaliseCluster,
)
from app.configuracao_geral.modelos_configuracao import (
    ConfiguracaoProcessamento,
    ConfiguracaoReducao,
    ConfiguracaoTecnicas,
    ParametrosDBSCAN,
    ParametrosHDBSCAN,
    ParametrosKMeans,
)
from app.configuracao_geral.tipos_enumerados import (
    AlgoritmoVizinhos,
    InicializacaoKMeans,
    MetricaDistancia,
    MetodoSelecaoCluster,
    StatusTendencia,
    TecnicaCluster,
    TecnicaReducao,
)


def test_protocolo_agrupador_generico_satisfacao() -> None:
    """Verifica que todos os agrupadores implementam ProtocoloAgrupador[TModelo]."""
    # 1. KMeans
    agrupador_km = AgrupadorKMeans(n_clusters=3, random_state=42)
    assert isinstance(agrupador_km, ProtocoloAgrupador)
    assert agrupador_km.obter_modelo() is None  # antes de fit

    # 2. DBSCAN
    agrupador_db = AgrupadorDBSCAN(eps=0.5, min_samples=3)
    assert isinstance(agrupador_db, ProtocoloAgrupador)
    assert agrupador_db.obter_modelo() is None

    # 3. HDBSCAN
    agrupador_hdb = AgrupadorHDBSCAN(min_cluster_size=5, min_samples=2)
    assert isinstance(agrupador_hdb, ProtocoloAgrupador)
    assert agrupador_hdb.obter_modelo() is None


def test_fabrica_agrupadores_tipagem_retorno() -> None:
    """Verifica a instanciação via fábrica devolvendo ProtocoloAgrupador."""
    config_proc = ConfiguracaoProcessamento(
        reducao=ConfiguracaoReducao(ativa=False, tecnica=TecnicaReducao.PCA, componentes=2),
        tecnicas=ConfiguracaoTecnicas(
            kmeans_ativo=True,
            kmeans_parametros=ParametrosKMeans(
                n_clusters=3,
                random_state=42,
                n_init=5,
                init=InicializacaoKMeans.KMEANS_PLUS_PLUS,
            ),
            dbscan_ativo=True,
            dbscan_parametros=ParametrosDBSCAN(
                eps=0.5,
                min_samples=2,
                metric=MetricaDistancia.EUCLIDEAN,
                algorithm=AlgoritmoVizinhos.AUTO,
            ),
            hdbscan_ativo=True,
            hdbscan_parametros=ParametrosHDBSCAN(
                min_cluster_size=2,
                min_samples=1,
                metric=MetricaDistancia.EUCLIDEAN,
                cluster_selection_method=MetodoSelecaoCluster.EOM,
            ),
        ),
    )

    agrupador = FabricaAgrupadores.criar_agrupador(TecnicaCluster.KMEANS, config_proc)
    assert isinstance(agrupador, ProtocoloAgrupador)

    dados = np.random.randn(20, 4)
    rotulos, metricas = agrupador.ajustar_e_agrupar(dados)
    assert len(rotulos) == 20
    assert metricas is not None
    modelo = agrupador.obter_modelo()
    assert isinstance(modelo, KMeans)


def test_resultado_tabular_generico() -> None:
    """Valida especialização genérica em ResultadoTecnicaTabular e ResultadoAgrupamentoTabular."""
    res_tec: ResultadoTecnicaTabular[KMeans] = ResultadoTecnicaTabular(
        tecnica="kmeans",
        rotulos=[0, 1, 0, 1],
        metricas=None,  # type: ignore[arg-type]
        modelo=KMeans(n_clusters=2),
    )
    assert res_tec.tecnica == "kmeans"
    assert isinstance(res_tec.modelo, KMeans)

    res_agrup: ResultadoAgrupamentoTabular[KMeans] = ResultadoAgrupamentoTabular(
        resultados={"kmeans": res_tec},
        n_amostras=4,
        n_features=2,
        reducao_aplicada=False,
    )
    assert "kmeans" in res_agrup.resultados
    assert isinstance(res_agrup.resultados["kmeans"].modelo, KMeans)


def test_estrategias_analise_genericas() -> None:
    """Valida EstrategiaAnaliseClusters com identificador genérico e Protocol."""
    # Instancia concreta de estratégia estática
    estrategia: EstrategiaAnaliseClusters[str] = EstrategiaAnaliseEstatica(minimo_amostras=2)
    assert isinstance(estrategia, EstrategiaAnaliseClusters)
    assert estrategia.eh_temporal() is False

    grupos = {"grupo_alpha": 10, "grupo_beta": 20}
    res: list[ResultadoAnaliseCluster[str]] = estrategia.analisar_grupos(grupos)
    assert len(res) == 2
    assert res[0].identificador in ["grupo_alpha", "grupo_beta"]
    assert res[0].status == StatusTendencia.ESTATICO
