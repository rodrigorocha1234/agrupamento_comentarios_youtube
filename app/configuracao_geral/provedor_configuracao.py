"""Provedor para carregamento e validação de configurações em YAML."""

from enum import StrEnum
from pathlib import Path
from typing import TypeVar, cast
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
from app.configuracao_geral.tipos_enumerados import (
    AlgoritmoVizinhos,
    DispositivoExecucao,
    GranularidadeTendencia,
    InicializacaoKMeans,
    MetricaDistancia,
    MetodoSelecaoCluster,
    MotorProcessamento,
    NormaVetorizacao,
    PeriodicidadeColeta,
    TecnicaReducao,
    TecnicaRepresentacao,
    TipoFonteDados,
    TipoPersistencia,
    TipoProvedorVisualizacao,
)

TEnum = TypeVar("TEnum", bound=StrEnum)


class ProvedorConfiguracaoErro(Exception):
    """Exceção levantada quando há falha no carregamento do arquivo de configuração."""


class ProvedorConfiguracao:
    """Carrega e valida o arquivo de configuração YAML gerando instâncias tipadas."""

    def __init__(self, caminho_arquivo: Path | str) -> None:
        self._caminho: Path = Path(caminho_arquivo)

    @staticmethod
    def _converter_enum(enum_cls: type[TEnum], valor: object, default: TEnum) -> TEnum:
        """Converte valor para o StrEnum informado de forma segura e com fallback padrão."""
        try:
            return enum_cls(str(valor).strip().lower())
        except (ValueError, KeyError, AttributeError):
            return default



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

            periodicidade = self._converter_enum(
                PeriodicidadeColeta,
                coleta_dict.get("periodicidade"),
                PeriodicidadeColeta.DIARIA,
            )
            fonte = self._converter_enum(
                TipoFonteDados,
                coleta_dict.get("fonte"),
                TipoFonteDados.YOUTUBE,
            )
            caminho_dados_raw = coleta_dict.get("caminho_dados")
            caminho_dados = str(caminho_dados_raw) if caminho_dados_raw else None
            coluna_texto = str(coleta_dict.get("coluna_texto", "texto"))
            coluna_id = str(coleta_dict.get("coluna_id", "id"))
            coluna_temporal_raw = coleta_dict.get("coluna_temporal")
            coluna_temporal = str(coluna_temporal_raw) if coluna_temporal_raw else None

            coleta_habilitada_padrao = "coleta" in dados
            coleta = ConfiguracaoColeta(
                habilitada=bool(coleta_dict.get("habilitada", coleta_habilitada_padrao)),
                fonte=fonte,
                periodicidade=periodicidade,
                canais=canais,
                dias_publicacao_atras=int(str(coleta_dict.get("dias_publicacao_atras", 7))),
                incluir_respostas=bool(coleta_dict.get("incluir_respostas", True)),
                tamanho_pagina=int(str(coleta_dict.get("tamanho_pagina", 100))),
                limite_videos_por_canal=limite_val,
                tentativas=int(str(coleta_dict.get("tentativas", 4))),
                atraso_base_segundos=float(str(coleta_dict.get("atraso_base_segundos", 2.0))),
                chave_api_env=str(coleta_dict.get("chave_api_env", "YOUTUBE_API_KEY")),
                caminho_dados=caminho_dados,
                coluna_texto=coluna_texto,
                coluna_id=coluna_id,
                coluna_temporal=coluna_temporal,
            )

            proc_dict = self._obter_dicionario(dados, "processamento")
            nlp_dict = self._obter_dicionario(proc_dict, "nlp")

            stop_dict = self._obter_dicionario(proc_dict, "stopwords") or self._obter_dicionario(nlp_dict, "stopwords")
            stopwords = ConfiguracaoStopwords(
                usar_spacy=bool(stop_dict.get("usar_spacy", True)),
                adicionais=[str(x) for x in self._obter_lista(stop_dict, "adicionais")],
                preservar=[str(x) for x in self._obter_lista(stop_dict, "preservar")],
                filtro_centroides=[str(x) for x in self._obter_lista(stop_dict, "filtro_centroides")],
            )

            rep_dict = self._obter_dicionario(proc_dict, "representacao") or self._obter_dicionario(nlp_dict, "representacao")
            ngram_raw = self._obter_lista(rep_dict, "ngram_range")
            ngram_val: tuple[int, int] = (
                int(str(ngram_raw[0])),
                int(str(ngram_raw[1])),
            ) if len(ngram_raw) >= 2 else (1, 2)
            tecnica_rep = self._converter_enum(
                TecnicaRepresentacao,
                rep_dict.get("tecnica"),
                TecnicaRepresentacao.TFIDF,
            )
            norma_rep = self._converter_enum(
                NormaVetorizacao,
                rep_dict.get("norma"),
                NormaVetorizacao.L2,
            )
            dispositivo_rep = self._converter_enum(
                DispositivoExecucao,
                rep_dict.get("dispositivo_transformers"),
                DispositivoExecucao.CPU,
            )
            representacao = ConfiguracaoRepresentacao(
                tecnica=tecnica_rep,
                min_df=int(str(rep_dict.get("min_df", 1))),
                max_df=float(str(rep_dict.get("max_df", 1.0))),
                ngram_range=ngram_val,
                sublinear_tf=bool(rep_dict.get("sublinear_tf", True)),
                norma=norma_rep,
                modelo_transformers=str(rep_dict.get("modelo_transformers", "neuralmind/bert-base-portuguese-cased")),
                dispositivo_transformers=dispositivo_rep,
                batch_size_transformers=int(str(rep_dict.get("batch_size_transformers", 32))),
            )

            red_dict = self._obter_dicionario(proc_dict, "reducao")
            tecnica_red = self._converter_enum(
                TecnicaReducao,
                red_dict.get("tecnica"),
                TecnicaReducao.SVD,
            )
            metrica_red = self._converter_enum(
                MetricaDistancia,
                red_dict.get("metrica"),
                MetricaDistancia.COSINE,
            )
            reducao = ConfiguracaoReducao(
                ativa=bool(red_dict.get("ativa", False)),
                tecnica=tecnica_red,
                componentes=int(str(red_dict.get("componentes", 100))),
                n_vizinhos=int(str(red_dict.get("n_vizinhos", 15))),
                distancia_minima=float(str(red_dict.get("distancia_minima", 0.0))),
                metrica=metrica_red,
                random_state=int(str(red_dict.get("random_state", 42))),
            )

            tec_dict = self._obter_dicionario(proc_dict, "tecnicas")
            km_dict = self._obter_dicionario(tec_dict, "kmeans")
            km_params = self._obter_dicionario(km_dict, "parametros")
            km_init = self._converter_enum(
                InicializacaoKMeans,
                km_params.get("init"),
                InicializacaoKMeans.KMEANS_PLUS_PLUS,
            )
            kmeans_parametros = ParametrosKMeans(
                n_clusters=int(str(km_params.get("n_clusters", 8))),
                random_state=int(str(km_params.get("random_state", 42))),
                n_init=int(str(km_params.get("n_init", 10))),
                init=km_init,
                k_automatico=bool(km_params.get("k_automatico", True)),
                k_min=int(str(km_params.get("k_min", 2))),
                k_max=int(str(km_params.get("k_max", 10))),
                max_iter=int(str(km_params.get("max_iter", 300))),
            )

            db_dict = self._obter_dicionario(tec_dict, "dbscan")
            db_params = self._obter_dicionario(db_dict, "parametros")
            db_metric = self._converter_enum(
                MetricaDistancia,
                db_params.get("metric"),
                MetricaDistancia.COSINE,
            )
            db_algo = self._converter_enum(
                AlgoritmoVizinhos,
                db_params.get("algorithm"),
                AlgoritmoVizinhos.AUTO,
            )
            dbscan_parametros = ParametrosDBSCAN(
                eps=float(str(db_params.get("eps", 0.5))),
                min_samples=int(str(db_params.get("min_samples", 5))),
                metric=db_metric,
                algorithm=db_algo,
            )

            hdb_dict = self._obter_dicionario(tec_dict, "hdbscan")
            hdb_params = self._obter_dicionario(hdb_dict, "parametros")
            hdb_metric = self._converter_enum(
                MetricaDistancia,
                hdb_params.get("metric"),
                MetricaDistancia.EUCLIDEAN,
            )
            hdb_method = self._converter_enum(
                MetodoSelecaoCluster,
                hdb_params.get("cluster_selection_method"),
                MetodoSelecaoCluster.EOM,
            )
            hdbscan_parametros = ParametrosHDBSCAN(
                min_cluster_size=int(str(hdb_params.get("min_cluster_size", 8))),
                min_samples=int(str(hdb_params.get("min_samples", 5))),
                metric=hdb_metric,
                cluster_selection_method=hdb_method,
            )

            tecnicas = ConfiguracaoTecnicas(
                kmeans_ativo=bool(km_dict.get("ativo", True)),
                kmeans_parametros=kmeans_parametros,
                dbscan_ativo=bool(db_dict.get("ativo", True)),
                dbscan_parametros=dbscan_parametros,
                hdbscan_ativo=bool(hdb_dict.get("ativo", True)),
                hdbscan_parametros=hdbscan_parametros,
            )

            motor_dados_str = str(proc_dict.get("motor_dados", "polars")).strip().lower()
            motor_dados = (
                MotorProcessamento.PANDAS
                if motor_dados_str == "pandas"
                else MotorProcessamento.POLARS
            )

            usar_nlp_bruto = proc_dict.get("usar_nlp", False)
            usar_nlp = (
                usar_nlp_bruto
                if isinstance(usar_nlp_bruto, bool)
                else str(usar_nlp_bruto).strip().lower() in ["true", "1", "sim", "yes"]
            )

            eh_temporal_bruto = proc_dict.get("eh_temporal", dados.get("eh_temporal", True))
            eh_temporal = (
                eh_temporal_bruto
                if isinstance(eh_temporal_bruto, bool)
                else str(eh_temporal_bruto).strip().lower() in ["true", "1", "sim", "yes"]
            )

            spacy_mod = str(proc_dict.get("spacy_modelo") or nlp_dict.get("spacy_modelo", "pt_core_news_sm"))

            processamento = ConfiguracaoProcessamento(
                reducao=reducao,
                tecnicas=tecnicas,
                spacy_modelo=spacy_mod,
                stopwords=stopwords,
                representacao=representacao,
                motor_dados=motor_dados,
                usar_nlp=usar_nlp,
                eh_temporal=eh_temporal,
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
            granularidade = self._converter_enum(
                GranularidadeTendencia,
                tend_dict.get("granularidade"),
                GranularidadeTendencia.DIARIA,
            )
            ativa_tend_bruto = tend_dict.get("ativa", eh_temporal)
            ativa_tendencias = (
                ativa_tend_bruto
                if isinstance(ativa_tend_bruto, bool)
                else str(ativa_tend_bruto).strip().lower() in ["true", "1", "sim", "yes"]
            )
            tendencias = ConfiguracaoTendencias(
                ativa=ativa_tendencias,
                janela_dias=int(str(tend_dict.get("janela_dias", 1))),
                minimo_comentarios=int(str(tend_dict.get("minimo_comentarios", 5))),
                crescimento_minimo_proporcao=float(str(tend_dict.get("crescimento_minimo_proporcao", 0.10))),
                queda_minima_proporcao=float(str(tend_dict.get("queda_minima_proporcao", 0.10))),
                max_amostras_video=int(str(tend_dict.get("max_amostras_video", 5))),
                max_amostras_canal=int(str(tend_dict.get("max_amostras_canal", 10))),
                granularidade=granularidade,
            )


            pers_dict = self._obter_dicionario(dados, "persistencia")
            caminhos_dict = self._obter_dicionario(pers_dict, "caminhos")
            prefixos_dict = self._obter_dicionario(pers_dict, "prefixos")
            caminho_bronze = str(caminhos_dict.get("bronze") or prefixos_dict.get("bronze", "bronze"))
            caminho_prata = str(caminhos_dict.get("prata") or prefixos_dict.get("prata", "prata"))
            caminho_ouro = str(caminhos_dict.get("ouro") or prefixos_dict.get("ouro", "ouro"))

            padroes_dict = self._obter_dicionario(pers_dict, "padroes_chaves")
            tipo_pers = self._converter_enum(
                TipoPersistencia,
                pers_dict.get("tipo"),
                TipoPersistencia.S3,
            )
            persistencia = ConfiguracaoPersistencia(
                tipo=tipo_pers,
                bucket=str(pers_dict.get("bucket", "youtube-comentarios")),
                prefixo_bronze=caminho_bronze,
                prefixo_prata=caminho_prata,
                prefixo_ouro=caminho_ouro,
                caminho_bronze=caminho_bronze,
                caminho_prata=caminho_prata,
                caminho_ouro=caminho_ouro,
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
            raw_provedor_vis = str(obs_dict.get("provedor_visualizacao", "")).lower()
            if raw_provedor_vis in [p.value for p in TipoProvedorVisualizacao]:
                provedor_vis = TipoProvedorVisualizacao(raw_provedor_vis)
            else:
                provedor_vis = (
                    TipoProvedorVisualizacao.GRAFANA
                    if bool(obs_dict.get("grafana", True))
                    else TipoProvedorVisualizacao.NENHUM
                )

            observabilidade = ConfiguracaoObservabilidade(
                prometheus=bool(obs_dict.get("prometheus", True)),
                grafana=bool(obs_dict.get("grafana", True)),
                labels_alta_cardinalidade=bool(obs_dict.get("labels_alta_cardinalidade", False)),
                provedor_visualizacao=provedor_vis,
                url_visualizacao=str(obs_dict.get("url_visualizacao", "http://localhost:3000")),
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
