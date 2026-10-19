"""Consolidação e agregação de tendências em nível de canal."""

from collections import Counter
from app.analise_tendencias.detector_variacao import DetectorVariacao
from app.gestao_dados.camada_ouro import RegistroTopicoOuro


class AgregadorVisoes:
    """Consolida os registros da camada Ouro de múltiplos vídeos em uma visão única por canal."""

    def __init__(
        self,
        detector: DetectorVariacao | None = None,
        max_amostras_canal: int = 10,
    ) -> None:
        self._detector: DetectorVariacao = detector or DetectorVariacao()
        self._max_amostras_canal: int = max_amostras_canal

    def consolidar_canal(
        self,
        id_canal: str,
        tecnica: str,
        topicos_dos_videos: list[RegistroTopicoOuro],
        janela: str = "",
    ) -> list[RegistroTopicoOuro]:
        """Agrega contagens e amostras de todos os vídeos de um canal sob a mesma técnica."""
        contagens_atuais: Counter[str] = Counter()
        contagens_anteriores: Counter[str] = Counter()
        amostras_canal: dict[str, list[str]] = {}

        for reg in topicos_dos_videos:
            topico = reg.topico
            contagens_atuais[topico] += reg.contagem_atual
            contagens_anteriores[topico] += reg.contagem_anterior

            if topico not in amostras_canal:
                amostras_canal[topico] = []
            if reg.comentarios_amostra:
                novas_amostras = (
                    reg.comentarios_amostra.split("|||")
                    if "|||" in reg.comentarios_amostra
                    else reg.comentarios_amostra.split(",")
                )
                for amostra in novas_amostras:
                    amostra_limpa = amostra.strip()
                    pode_adicionar = (
                        self._max_amostras_canal <= 0
                        or len(amostras_canal[topico]) < self._max_amostras_canal
                    )
                    if (
                        amostra_limpa
                        and amostra_limpa not in amostras_canal[topico]
                        and pode_adicionar
                    ):
                        amostras_canal[topico].append(amostra_limpa)

        todos_topicos = set(contagens_atuais.keys()) | set(contagens_anteriores.keys())
        consolidados: list[RegistroTopicoOuro] = []
        data_ref = (
            topicos_dos_videos[0].data_referencia
            if topicos_dos_videos and topicos_dos_videos[0].data_referencia
            else ""
        )

        for topico in sorted(todos_topicos):
            c_atual = contagens_atuais[topico]
            c_anterior = contagens_anteriores[topico]
            res_var = self._detector.classificar(c_atual, c_anterior)
            amostras_str = "|||".join(amostras_canal.get(topico, []))

            consolidados.append(
                RegistroTopicoOuro(
                    id_canal=id_canal,
                    id_video="consolidado",
                    tecnica=tecnica,
                    topico=topico,
                    contagem_atual=res_var.contagem_atual,
                    contagem_anterior=res_var.contagem_anterior,
                    variacao_proporcao=res_var.variacao_proporcao,
                    status_tendencia=res_var.status_tendencia,
                    comentarios_amostra=amostras_str,
                    janela=janela,
                    data_referencia=data_ref,
                    percentual_variacao=res_var.percentual_variacao,
                )
            )

        return consolidados
