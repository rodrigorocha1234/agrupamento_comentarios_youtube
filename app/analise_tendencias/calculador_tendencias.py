"""Cálculo e comparação de tendências de tópicos entre janelas temporais."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.analise_tendencias.detector_variacao import (
    DetectorVariacao,
    ResultadoVariacao,
)
from app.coleta_youtube.modelos_coleta import ComentarioColetado
from app.gestao_dados.camada_ouro import RegistroTopicoOuro


@dataclass(frozen=True, slots=True)
class TopicoComentarios:
    """Associação entre um tópico, os comentários vinculados e sua classificação."""

    topico: str
    resultado_variacao: ResultadoVariacao
    ids_amostra: list[str]


class CalculadorTendencias:
    """Calcula a variação temporal de tópicos por dia (série temporal Hoje vs Ontem) ou janela."""

    def __init__(
        self,
        janela_dias: int = 1,
        detector: DetectorVariacao | None = None,
        max_amostras_video: int = 5,
        granularidade: str | None = None,
    ) -> None:
        self._janela_dias: int = max(1, janela_dias)
        self._detector: DetectorVariacao = detector or DetectorVariacao()
        self._max_amostras_video: int = max_amostras_video
        if granularidade is not None:
            self._granularidade: str = granularidade
        else:
            self._granularidade: str = "diaria" if self._janela_dias == 1 else "janela"

    def calcular_tendencias_video(
        self,
        id_canal: str,
        id_video: str,
        tecnica: str,
        topicos_por_comentario: dict[str, str],
        comentarios: list[ComentarioColetado],
        referencia_temporal: datetime | None = None,
    ) -> list[RegistroTopicoOuro]:
        """Calcula a série temporal diária de cada tópico (Hoje vs Ontem) e gera registros para camada Ouro."""
        agora = referencia_temporal or datetime.now(timezone.utc)
        data_referencia = agora.strftime("%Y-%m-%d")

        if self._granularidade == "diaria":
            # Granularidade diária pontual: Hoje (00h às 23h59) vs Ontem (00h às 23h59)
            inicio_hoje = datetime(agora.year, agora.month, agora.day, tzinfo=timezone.utc)
            inicio_ontem = inicio_hoje - timedelta(days=1)
            inicio_atual = inicio_hoje
            inicio_anterior = inicio_ontem
            fim_anterior = inicio_hoje
            rotulo_janela = "diaria"
        else:
            inicio_atual = agora - timedelta(days=self._janela_dias)
            inicio_anterior = inicio_atual - timedelta(days=self._janela_dias)
            fim_anterior = inicio_atual
            rotulo_janela = f"{self._janela_dias}dias"

        contagem_atual: Counter[str] = Counter()
        contagem_anterior: Counter[str] = Counter()
        amostras_por_topico: dict[str, list[str]] = {}

        # Ordena decrescentemente para priorizar comentários mais recentes
        comentarios_ordenados = sorted(comentarios, key=lambda c: c.publicado_em, reverse=True)

        for com in comentarios_ordenados:
            topico = topicos_por_comentario.get(com.id_comentario, "sem_topico")
            if topico not in amostras_por_topico:
                amostras_por_topico[topico] = []

            pode_adicionar = (
                self._max_amostras_video <= 0
                or len(amostras_por_topico[topico]) < self._max_amostras_video
            )
            if pode_adicionar:
                texto_limpo = (
                    com.texto_original.strip()
                    .replace("\r\n", " ")
                    .replace("\n", " ")
                    .replace("\r", " ")
                    .replace("|||", " ")
                )
                if texto_limpo and texto_limpo not in amostras_por_topico[topico]:
                    amostras_por_topico[topico].append(texto_limpo)

            if com.publicado_em >= inicio_atual:
                contagem_atual[topico] += 1
            elif com.publicado_em >= inicio_anterior and com.publicado_em < fim_anterior:
                contagem_anterior[topico] += 1

        todos_topicos = (
            set(topicos_por_comentario.values())
            | set(contagem_atual.keys())
            | set(contagem_anterior.keys())
        )
        registros_ouro: list[RegistroTopicoOuro] = []

        for topico in sorted(todos_topicos):
            c_atual = contagem_atual[topico]
            c_anterior = contagem_anterior[topico]
            res_var = self._detector.classificar(c_atual, c_anterior)
            amostras_str = "|||".join(amostras_por_topico.get(topico, []))

            registros_ouro.append(
                RegistroTopicoOuro(
                    id_canal=id_canal,
                    id_video=id_video,
                    tecnica=tecnica,
                    topico=topico,
                    contagem_atual=res_var.contagem_atual,
                    contagem_anterior=res_var.contagem_anterior,
                    variacao_proporcao=res_var.variacao_proporcao,
                    status_tendencia=res_var.status_tendencia,
                    comentarios_amostra=amostras_str,
                    janela=rotulo_janela,
                    data_referencia=data_referencia,
                    percentual_variacao=res_var.percentual_variacao,
                )
            )

        return registros_ouro

