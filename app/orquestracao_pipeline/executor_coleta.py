"""Orquestrador do ciclo de extração paginada, validação, staging transacional e outbox."""

import json
import time
import uuid
from datetime import UTC, datetime
from typing import final

from app.configuracao_geral.conf_yaml import ConfYAML
from app.dominio_contratos.modelos_dados import (
    EventoPublicacao,
    MetadadosExecucao,
)
from app.dominio_contratos.protocolos_staging import RepositorioStaging, UnidadeTrabalho
from app.extracao_steam.gerador_paginas import GeradorPaginasSteam
from app.gestao_datalake.despachante_outbox import DespachanteOutbox
from app.gestao_datalake.escritor_prata import EscritorCamadaPrata
from app.observabilidade_metricas.registro_telemetria import RegistroTelemetria
from app.observabilidade_metricas.validador_qualidade import ValidadorQualidadeDados


@final
class ExecutorColetaStaging:
    """Coordena o fluxo de ponta a ponta com backpressure e atomicidade por lote."""

    def __init__(
        self,
        configuracoes: ConfYAML,
        gerador_paginas: GeradorPaginasSteam,
        uow: UnidadeTrabalho,
        repositorio: RepositorioStaging,
        despachante_outbox: DespachanteOutbox | None = None,
        escritor_prata: EscritorCamadaPrata | None = None,
        validador: ValidadorQualidadeDados | None = None,
        telemetria: RegistroTelemetria | None = None,
    ) -> None:
        self._config = configuracoes
        self._gerador = gerador_paginas
        self._uow = uow
        self._repositorio = repositorio
        self._despachante = despachante_outbox
        self._escritor_prata = escritor_prata
        self._validador = validador or ValidadorQualidadeDados()
        self._telemetria = telemetria or RegistroTelemetria()

    def executar_coleta_jogo(
        self, appid: int, estrategia: str = "recente"
    ) -> MetadadosExecucao:
        """Executa a coleta completa de um jogo, respeitando checkpoints e lotes."""
        id_execucao = str(uuid.uuid4())
        inicio = datetime.now(UTC)
        total_paginas = 0
        total_reviews = 0

        metadados = MetadadosExecucao(
            id_execucao=id_execucao,
            appid=appid,
            estrategia=estrategia,
            data_inicio=inicio,
            data_fim=None,
            status="em_execucao",
            total_paginas=0,
            total_reviews=0,
        )

        with self._uow:
            self._repositorio.registrar_execucao(metadados)

        cursor_inicial = (
            self._repositorio.obter_ultimo_checkpoint(appid, estrategia) or "*"
        )

        try:
            for pagina in self._gerador.iterar_paginas(
                appid, cursor_inicial=cursor_inicial
            ):
                inicio_lote = time.perf_counter()

                # Quality Gate
                relatorio = self._validador.validar_lote_reviews(pagina.reviews)
                if not relatorio.aprovado:
                    motivo = "; ".join(relatorio.mensagens_bloqueantes)
                    raise ValueError(
                        f"Quality Gate rejeitou página de reviews: {motivo}"
                    )

                # Transação atômica por página / lote
                with self._uow:
                    self._repositorio.gravar_pagina(pagina, id_execucao)
                    self._repositorio.salvar_lote_reviews(pagina.reviews)

                    # Enfileirar evento outbox para gravação Bronze
                    evento_bronze = EventoPublicacao(
                        id_evento=str(uuid.uuid4()),
                        tipo_evento="bronze_pagina",
                        chave_origem=f"bronze/steam/reviews/appid={appid}/execucao={id_execucao}/pagina_{total_paginas:04d}.json",
                        payload_referencia=json.dumps(
                            {
                                "appid": appid,
                                "hash": pagina.hash_payload,
                                "total": pagina.total_reviews_pagina,
                            }
                        ),
                        status_publicacao="pendente",
                        tentativas=0,
                        data_criacao=datetime.now(UTC),
                    )
                    self._repositorio.enfileirar_evento_outbox(evento_bronze)

                    # Gravação colunar Silver se escritor estiver disponível
                    if self._escritor_prata is not None and pagina.reviews:
                        self._escritor_prata.salvar_lote_parquet(
                            appid=appid,
                            identificador_lote=f"{id_execucao}_{total_paginas:04d}",
                            reviews=pagina.reviews,
                        )

                    proximo = pagina.cursor_proximo or cursor_inicial
                    self._repositorio.atualizar_checkpoint(
                        appid=appid,
                        estrategia=estrategia,
                        cursor=proximo,
                        status="ativo",
                    )

                duracao_lote = time.perf_counter() - inicio_lote
                self._telemetria.registrar_lote(appid, "sqlite", duracao_lote)
                self._telemetria.registrar_pagina(appid, True)

                total_paginas += 1
                total_reviews += len(pagina.reviews)

            # Sucesso
            fim = datetime.now(UTC)
            resultado = MetadadosExecucao(
                id_execucao=id_execucao,
                appid=appid,
                estrategia=estrategia,
                data_inicio=inicio,
                data_fim=fim,
                status="concluido",
                total_paginas=total_paginas,
                total_reviews=total_reviews,
            )
            with self._uow:
                self._repositorio.registrar_execucao(resultado)

            # Despacho da outbox após o encerramento dos lotes
            if self._despachante is not None:
                self._despachante.executar_ciclo_publicacao(limite_lote=500)

            return resultado

        except Exception as erro:
            fim = datetime.now(UTC)
            falha = MetadadosExecucao(
                id_execucao=id_execucao,
                appid=appid,
                estrategia=estrategia,
                data_inicio=inicio,
                data_fim=fim,
                status="falhou",
                total_paginas=total_paginas,
                total_reviews=total_reviews,
                mensagem_erro=str(erro),
            )
            with self._uow:
                self._repositorio.registrar_execucao(falha)
            self._telemetria.registrar_pagina(appid, False)
            raise
