"""Provedor para carregamento e validação de configurações em YAML."""

from pathlib import Path
from typing import cast
import yaml

from app.configuracao_geral.modelos_configuracao import (
    CanalConfigurado,
    ConfiguracaoAPI,
    ConfiguracaoColeta,
    ConfiguracaoGlobal,
    ConfiguracaoMLflow,
    ConfiguracaoObservabilidade,
    ConfiguracaoPersistencia,
    ConfiguracaoProcessamento,
    ConfiguracaoProjeto,
    ConfiguracaoReducao,
    ConfiguracaoRepresentacao,
    ConfiguracaoStopwords,
    ConfiguracaoTecnicas,
    ConfiguracaoTendencias,
    ConfiguracaoTopicos,
    ParametrosDBSCAN,
    ParametrosHDBSCAN,
    ParametrosKMeans,
)


class ProvedorConfiguracaoErro(Exception):
    """Exceção levantada quando há falha no carregamento do arquivo de configuração."""


class ProvedorConfiguracao:
    """Carrega e valida o arquivo de configuração YAML gerando instâncias tipadas."""

    def __init__(self, caminho_arquivo: Path | str) -> None:
        self._caminho: Path = Path(caminho_arquivo)

    def carregar(self) -> ConfiguracaoGlobal:
        """Lê o arquivo YAML e mapeia em estruturas imutáveis tipadas.

        Returns:
            ConfiguracaoGlobal: Estrutura completa de configurações tipadas.

        Raises:
            ProvedorConfiguracaoErro: Caso o arquivo não exista ou contenha valores inválidos.
        """
        if not self._caminho.exists():
            raise ProvedorConfiguracaoErro(
                f"Arquivo de configuração não encontrado: {self._caminho}"
            )

        try:
            with self._caminho.open("r", encoding="utf-8") as descritor:
                conteudo_bruto: object = yaml.safe_load(descritor)
        except Exception as erro:
            raise ProvedorConfiguracaoErro(
                f"Erro ao analisar o arquivo YAML {self._caminho}: {erro}"
            ) from erro

        if not isinstance(conteudo_bruto, dict):
            raise ProvedorConfiguracaoErro("Conteúdo YAML deve ser um mapeamento dicionário.")

        dados_dict = cast(dict[str, object], conteudo_bruto)
        return self._construir_configuracao(dados_dict)

    def _construir_configuracao(self, dados: dict[str, object]) -> ConfiguracaoGlobal:
        """Valida recursivamente as seções do dicionário e monta o objeto tipado."""
        try:
            proj_dict = self._obter_dicionario(dados, "projeto")
            projeto = ConfiguracaoProjeto(
                nome=str(proj_dict.get("nome", "agrupamento_comentarios_youtube")),
                idioma=str(proj_dict.get("idioma", "pt_BR")),
            )

            coleta_dict = self._obter_dicionario(dados, "coleta")
            canais_lista = self._obter_lista(coleta_dict, "canais")
            canais: list[CanalConfigurado] = []
            for item in canais_lista:
                if isinstance(item, dict):
                    item_dict = cast(dict[str, object], item)
                    canais.append(
                        CanalConfigurado(
                            id_canal=str(item_dict.get("id_canal", "")),
                            ativo=bool(item_dict.get("ativo", False)),
                        )
                    )

            limite_videos = coleta_dict.get("limite_videos_por_canal")
            limite_val: int | None = int(limite_videos) if isinstance(limite_videos, int) else None

            coleta = ConfiguracaoColeta(
                habilitada=bool(coleta_dict.get("habilitada", True)),
                periodicidade=str(coleta_dict.get("periodicidade", "diaria")),
                canais=canais,
                dias_publicacao_atras=int(str(coleta_dict.get("dias_publicacao_atras", 7))),
                incluir_respostas=bool(coleta_dict.get("incluir_respostas", True)),
                tamanho_pagina=int(str(coleta_dict.get("tamanho_pagina", 100))),
                limite_videos_por_canal=limite_val,
                tentativas=int(str(coleta_dict.get("tentativas", 4))),
                atraso_base_segundos=float(str(coleta_dict.get("atraso_base_segundos", 2.0))),
                chave_api_env=str(coleta_dict.get("chave_api_env", "YOUTUBE_API_KEY")),
            )

            proc_dict = self._obter_dicionario(dados, "processamento")
            stop_dict = self._obter_dicionario(proc_dict, "stopwords")
            stopwords = ConfiguracaoStopwords(
                usar_spacy=bool(stop_dict.get("usar_spacy", True)),
                adicionais=[str(x) for x in self._obter_lista(stop_dict, "adicionais")],
                preservar=[str(x) for x in self._obter_lista(stop_dict, "preservar")],
                filtro_centroides=[str(x) for x in self._obter_lista(stop_dict, "filtro_centroides")],
            )

            rep_dict = self._obter_dicionario(proc_dict, "representacao")
            ngram_raw = self._obter_lista(rep_dict, "ngram_range")
            ngram_val: tuple[int, int] = (
                int(str(ngram_raw[0])),
                int(str(ngram_raw[1])),
            ) if len(ngram_raw) >= 2 else (1, 2)
            representacao = ConfiguracaoRepresentacao(
                tecnica=str(rep_dict.get("tecnica", "tfidf")),
                min_df=int(str(rep_dict.get("min_df", 2))),
                max_df=float(str(rep_dict.get("max_df", 0.95))),
                ngram_range=ngram_val,
                sublinear_tf=bool(rep_dict.get("sublinear_tf", True)),
                norma=str(rep_dict.get("norma", "l2")),
                modelo_transformers=str(rep_dict.get("modelo_transformers", "neuralmind/bert-base-portuguese-cased")),
                dispositivo_transformers=str(rep_dict.get("dispositivo_transformers", "cpu")),
                batch_size_transformers=int(str(rep_dict.get("batch_size_transformers", 32))),
            )

            red_dict = self._obter_dicionario(proc_dict, "reducao")
            reducao = ConfiguracaoReducao(
                ativa=bool(red_dict.get("ativa", False)),
                tecnica=str(red_dict.get("tecnica", "svd")),
                componentes=int(str(red_dict.get("componentes", 100))),
                n_vizinhos=int(str(red_dict.get("n_vizinhos", 15))),
                distancia_minima=float(str(red_dict.get("distancia_minima", 0.0))),
                metrica=str(red_dict.get("metrica", "cosine")),
                random_state=int(str(red_dict.get("random_state", 42))),
            )

            tec_dict = self._obter_dicionario(proc_dict, "tecnicas")
            km_dict = self._obter_dicionario(tec_dict, "kmeans")
            km_params = self._obter_dicionario(km_dict, "parametros")
            kmeans_parametros = ParametrosKMeans(
                n_clusters=int(str(km_params.get("n_clusters", 8))),
                random_state=int(str(km_params.get("random_state", 42))),
                n_init=int(str(km_params.get("n_init", 10))),
                k_automatico=bool(km_params.get("k_automatico", True)),
                k_min=int(str(km_params.get("k_min", 2))),
                k_max=int(str(km_params.get("k_max", 10))),
                max_iter=int(str(km_params.get("max_iter", 300))),
            )

            db_dict = self._obter_dicionario(tec_dict, "dbscan")
            db_params = self._obter_dicionario(db_dict, "parametros")
            dbscan_parametros = ParametrosDBSCAN(
                eps=float(str(db_params.get("eps", 0.5))),
                min_samples=int(str(db_params.get("min_samples", 5))),
                metric=str(db_params.get("metric", "cosine")),
                algorithm=str(db_params.get("algorithm", "auto")),
            )

            hdb_dict = self._obter_dicionario(tec_dict, "hdbscan")
            hdb_params = self._obter_dicionario(hdb_dict, "parametros")
            hdbscan_parametros = ParametrosHDBSCAN(
                min_cluster_size=int(str(hdb_params.get("min_cluster_size", 8))),
                min_samples=int(str(hdb_params.get("min_samples", 5))),
                metric=str(hdb_params.get("metric", "euclidean")),
                cluster_selection_method=str(hdb_params.get("cluster_selection_method", "eom")),
            )

            tecnicas = ConfiguracaoTecnicas(
                kmeans_ativo=bool(km_dict.get("ativo", True)),
                kmeans_parametros=kmeans_parametros,
                dbscan_ativo=bool(db_dict.get("ativo", True)),
                dbscan_parametros=dbscan_parametros,
                hdbscan_ativo=bool(hdb_dict.get("ativo", True)),
                hdbscan_parametros=hdbscan_parametros,
            )

            processamento = ConfiguracaoProcessamento(
                spacy_modelo=str(proc_dict.get("spacy_modelo", "pt_core_news_sm")),
                stopwords=stopwords,
                representacao=representacao,
                reducao=reducao,
                tecnicas=tecnicas,
            )

            top_dict = self._obter_dicionario(dados, "topicos")
            topicos = ConfiguracaoTopicos(
                pos_permitidas=[str(x) for x in self._obter_lista(top_dict, "pos_permitidas")],
                comprimento_minimo=int(str(top_dict.get("comprimento_minimo", 3))),
                peso_tfidf=float(str(top_dict.get("peso_tfidf", 0.7))),
                peso_frequencia=float(str(top_dict.get("peso_frequencia", 0.3))),
                penalizacao_global=bool(top_dict.get("penalizacao_global", True)),
                limiar_penalizacao_global=float(str(top_dict.get("limiar_penalizacao_global", 0.75))),
                fator_penalidade=float(str(top_dict.get("fator_penalidade", 0.2))),
                rotulo_ruido_padrao=str(top_dict.get("rotulo_ruido_padrao", "sem_topico")),
            )

            tend_dict = self._obter_dicionario(dados, "tendencias")
            tendencias = ConfiguracaoTendencias(
                janela_dias=int(str(tend_dict.get("janela_dias", 1))),
                minimo_comentarios=int(str(tend_dict.get("minimo_comentarios", 5))),
                crescimento_minimo_proporcao=float(str(tend_dict.get("crescimento_minimo_proporcao", 0.10))),
                queda_minima_proporcao=float(str(tend_dict.get("queda_minima_proporcao", 0.10))),
                max_amostras_video=int(str(tend_dict.get("max_amostras_video", 5))),
                max_amostras_canal=int(str(tend_dict.get("max_amostras_canal", 10))),
                granularidade=str(tend_dict.get("granularidade", "diaria")),
            )


            pers_dict = self._obter_dicionario(dados, "persistencia")
            prefixos_dict = self._obter_dicionario(pers_dict, "prefixos")
            padroes_dict = self._obter_dicionario(pers_dict, "padroes_chaves")
            persistencia = ConfiguracaoPersistencia(
                tipo=str(pers_dict.get("tipo", "s3")),
                bucket=str(pers_dict.get("bucket", "youtube-comentarios")),
                prefixo_bronze=str(prefixos_dict.get("bronze", "bronze")),
                prefixo_prata=str(prefixos_dict.get("prata", "prata")),
                prefixo_ouro=str(prefixos_dict.get("ouro", "ouro")),
                endpoint_env=str(pers_dict.get("endpoint_env", "S3_ENDPOINT_URL")),
                access_key_env=str(pers_dict.get("access_key_env", "AWS_ACCESS_KEY_ID")),
                secret_key_env=str(pers_dict.get("secret_key_env", "AWS_SECRET_ACCESS_KEY")),
                padrao_chave_bronze=str(
                    padroes_dict.get(
                        "bronze",
                        "{prefixo}/id_canal={id_canal}/id_video={id_video}/data_coleta={data_coleta}/lote={id_lote}.jsonl",
                    )
                ),
                padrao_chave_prata=str(
                    padroes_dict.get(
                        "prata",
                        "{prefixo}/id_canal={id_canal}/id_video={id_video}/versao={timestamp_versao}/comentarios.parquet",
                    )
                ),
                padrao_chave_ouro_video=str(
                    padroes_dict.get(
                        "ouro_video",
                        "{prefixo}/id_canal={id_canal}/id_video={id_video}/tecnica={tecnica}/data={data_referencia}/topicos.parquet",
                    )
                ),
                padrao_chave_ouro_consolidado=str(
                    padroes_dict.get(
                        "ouro_consolidado",
                        "{prefixo}/id_canal={id_canal}/consolidado/tecnica={tecnica}/data={data_referencia}/topicos.parquet",
                    )
                ),
            )

            mlf_dict = self._obter_dicionario(dados, "mlflow")
            mlflow = ConfiguracaoMLflow(
                tracking_uri_env=str(mlf_dict.get("tracking_uri_env", "MLFLOW_TRACKING_URI")),
                serving_url_env=str(mlf_dict.get("serving_url_env", "MLFLOW_SERVING_URL")),
            )

            api_dict = self._obter_dicionario(dados, "api")
            cors_lista = [str(x) for x in self._obter_lista(api_dict, "cors_origens")]
            if not cors_lista:
                cors_lista = ["*"]
            api = ConfiguracaoAPI(
                porta=int(str(api_dict.get("porta", 8000))),
                tempo_limite_segundos=float(str(api_dict.get("tempo_limite_segundos", 30.0))),
                cors_origens=cors_lista,
                top_termos_padrao=int(str(api_dict.get("top_termos_padrao", 5))),
                tamanho_pagina_padrao=int(str(api_dict.get("tamanho_pagina_padrao", 10))),
                tamanho_pagina_maximo=int(str(api_dict.get("tamanho_pagina_maximo", 100))),
            )

            obs_dict = self._obter_dicionario(dados, "observabilidade")
            observabilidade = ConfiguracaoObservabilidade(
                prometheus=bool(obs_dict.get("prometheus", True)),
                grafana=bool(obs_dict.get("grafana", True)),
                labels_alta_cardinalidade=bool(obs_dict.get("labels_alta_cardinalidade", False)),
            )

            return ConfiguracaoGlobal(
                projeto=projeto,
                coleta=coleta,
                processamento=processamento,
                topicos=topicos,
                tendencias=tendencias,
                persistencia=persistencia,
                mlflow=mlflow,
                api=api,
                observabilidade=observabilidade,
            )
        except Exception as erro:
            raise ProvedorConfiguracaoErro(f"Estrutura inválida no arquivo de configuração: {erro}") from erro

    @staticmethod
    def _obter_dicionario(origem: dict[str, object], chave: str) -> dict[str, object]:
        """Extrai um sub-dicionário ou retorna dicionário vazio."""
        valor = origem.get(chave)
        if isinstance(valor, dict):
            return cast(dict[str, object], valor)
        return {}

    @staticmethod
    def _obter_lista(origem: dict[str, object], chave: str) -> list[object]:
        """Extrai uma sub-lista ou retorna lista vazia."""
        valor = origem.get(chave)
        if isinstance(valor, list):
            return cast(list[object], valor)
        return []
