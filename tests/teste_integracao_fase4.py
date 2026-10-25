"""Testes integrados de ponta a ponta da Fase 4: Lakehouse Gold, Telemetria e Negócio."""

from typing import final, override

import pandas as pd
from prometheus_client import CollectorRegistry

from app.configuracao_geral.conf_yaml import ConfYAML
from app.dominio_contratos.protocolos_datalake import ArmazenamentoLake
from app.gestao_datalake.escritor_ouro import EscritorCamadaOuro
from app.observabilidade_metricas.telemetria_analitica import TelemetriaAnalitica
from app.regras_negocio.rotulador_clusters import RotuladorClusters
from app.treinamento_pipeline.executor_treinamento import ExecutorTreinamento
from app.treinamento_pipeline.exportador_ouro import ExportadorCamadaOuro
from app.visualizacao_dados.painel_executivo import PainelExecutivo


@final
class ArmazenamentoLakeFalso(ArmazenamentoLake):
    """Armazenamento simulado para validação do Lakehouse Gold."""

    def __init__(self) -> None:
        self.textos: dict[str, str] = {}
        self.arquivos_binarios: dict[str, bytes] = {}

    @property
    @override
    def bucket(self) -> str:
        return "steam-reviews-teste"

    @override
    def gravar_texto(self, caminho_chave: str, conteudo: str) -> None:
        self.textos[caminho_chave] = conteudo

    @override
    def gravar_bytes(self, caminho_chave: str, dados_bytes: bytes) -> None:
        self.arquivos_binarios[caminho_chave] = dados_bytes

    @override
    def ler_bytes(self, caminho_chave: str) -> bytes:
        if caminho_chave in self.arquivos_binarios:
            return self.arquivos_binarios[caminho_chave]
        if caminho_chave in self.textos:
            return self.textos[caminho_chave].encode("utf-8")
        raise FileNotFoundError(f"Chave '{caminho_chave}' não encontrada.")

    @override
    def listar_chaves(self, prefixo: str) -> list[str]:
        prefixo_limpo = prefixo.lstrip("/")
        todas = list(self.arquivos_binarios.keys()) + list(self.textos.keys())
        return [k for k in todas if k.lstrip("/").startswith(prefixo_limpo)]

    @override
    def verificar_existencia(self, caminho_chave: str) -> bool:
        return caminho_chave in self.textos or caminho_chave in self.arquivos_binarios


def teste_integracao_fase4_ponta_a_ponta() -> None:
    """Valida o ciclo completo da Fase 4: regras YAML, treinamento, lake Gold e telemetria."""
    # 1. Carregamento de configuração declarativa
    conf = ConfYAML()
    assert conf.negocio.negocio.ativado is True
    assert len(conf.negocio.negocio.regras) >= 5

    # 2. Compilação do rotulador GoF de personas
    definicoes_regras = [r.model_dump() for r in conf.negocio.negocio.regras]
    rotulador = RotuladorClusters.de_configuracao(definicoes_regras)

    # 3. Preparação do pipeline e dados sintéticos Silver
    painel = PainelExecutivo()
    executor = ExecutorTreinamento(
        configuracoes=conf,
        rotulador_negocio=rotulador,
        painel_executivo=painel,
    )

    tamanho = 120
    df_silver = pd.DataFrame(
        {
            "recommendationid": [f"rec_{i}" for i in range(tamanho)],
            "voted_up": [True] * 80 + [False] * 40,
            "votes_up": [10] * 60 + [0] * 60,
            "playtime_forever": [12000] * 60 + [300] * 60,
            "playtime_last_two_weeks": [60] * tamanho,
            "playtime_at_review": [10000] * 60 + [250] * 60,
            "num_games_owned": [50] * tamanho,
            "num_reviews": [5] * tamanho,
            "timestamp_created": [1680000000 + i * 3600 for i in range(tamanho)],
            "last_played": [1690000000 + i * 3600 for i in range(tamanho)],
            "review_texto": ["Texto original para consulta humana"] * tamanho,
        }
    )

    # 4. Treinamento de clustering e avaliação estatística
    dados_gold, avaliacao, _ = executor.executar_treinamento(
        dados_silver=df_silver,
        nome_algoritmo="kmeans",
        parametros_algoritmo={"n_clusters": 2, "n_init": 10},
        versao_dataset="gold_v4_test",
    )

    assert "cluster_id" in dados_gold.columns
    assert "rotulo_negocio" in dados_gold.columns
    assert avaliacao.total_clusters == 2

    # 5. Exportador para a Camada Gold e Telemetria
    lake = ArmazenamentoLakeFalso()
    escritor_ouro = EscritorCamadaOuro(lake)
    registry = CollectorRegistry()
    telemetria = TelemetriaAnalitica(registry=registry)
    exportador = ExportadorCamadaOuro(
        escritor_ouro=escritor_ouro,
        telemetria_analitica=telemetria,
        painel_executivo=painel,
    )

    resultados_exportacao = exportador.exportar_camada_ouro(
        appid=427520,
        nome_algoritmo="kmeans",
        versao="v4_integrado",
        dados_gold=dados_gold,
        avaliacao=avaliacao,
        mapa_rotulos_negocio={0: "Veteranos Leais", 1: "Novatos Satisfeitos"},
        hash_execucao=conf.hash_configuracao,
    )

    # 6. Validação dos artefatos persistidos no Lakehouse
    caminho_clusters = resultados_exportacao["clusters_parquet"]
    caminho_metricas = resultados_exportacao["metricas_parquet"]
    caminho_resumo = resultados_exportacao["resumo_json"]
    caminho_manifesto = resultados_exportacao["manifesto_json"]

    assert caminho_clusters in lake.arquivos_binarios
    assert caminho_metricas in lake.arquivos_binarios
    assert caminho_resumo in lake.textos
    assert caminho_manifesto in lake.textos

    # 7. Validação de telemetria nos contadores e gauges
    val_clusters = registry.get_sample_value(
        "steam_clusters_total", {"appid": "427520", "algoritmo": "kmeans"}
    )
    assert val_clusters == 2.0

    val_parquet = registry.get_sample_value(
        "steam_gold_gravacoes_total",
        {"appid": "427520", "tipo_artefato": "clusters_parquet"},
    )
    assert val_parquet == 1.0

    # 8. Validação do relatório executivo gerado
    relatorio = resultados_exportacao["relatorio_markdown"]
    assert "Relatório Executivo de Agrupamento" in relatorio
    assert "KMEANS" in relatorio
