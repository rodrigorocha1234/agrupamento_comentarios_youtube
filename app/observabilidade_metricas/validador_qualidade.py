"""Quality Gate para validação de unicidade, schema e consistência das avaliações."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final

from app.dominio_contratos.modelos_dados import ReviewSteam


@dataclass(frozen=True, slots=True)
class RelatorioQualidade:
    """Resultado estruturado da validação de qualidade de dados."""

    aprovado: bool
    total_registros: int
    total_duplicados: int
    total_inconsistencias_temporais: int
    total_valores_invalidos: int
    mensagens_bloqueantes: tuple[str, ...]
    avisos: tuple[str, ...]


@final
class ValidadorQualidadeDados:
    """Aplica regras do Quality Gate para dados brutos e normalizados."""

    def validar_lote_reviews(
        self, reviews: Sequence[ReviewSteam]
    ) -> RelatorioQualidade:
        """Checa integridade estrutural, unicidade e regras de domínio."""
        if not reviews:
            return RelatorioQualidade(
                aprovado=True,
                total_registros=0,
                total_duplicados=0,
                total_inconsistencias_temporais=0,
                total_valores_invalidos=0,
                mensagens_bloqueantes=(),
                avisos=("Lote vazio recebido para validação.",),
            )

        chaves_vistas: set[tuple[int, str]] = set()
        duplicados = 0
        inconsistencias_temporais = 0
        valores_invalidos = 0
        bloqueios: list[str] = []
        avisos: list[str] = []

        for r in reviews:
            # Checagem de unicidade (appid, recommendationid)
            chave = (r.appid, r.recommendationid)
            if chave in chaves_vistas:
                duplicados += 1
            else:
                chaves_vistas.add(chave)

            # Consistência temporal
            if r.timestamp_created > r.timestamp_updated and r.timestamp_updated > 0:
                inconsistencias_temporais += 1

            # Domínios numéricos
            if r.author.playtime_forever < 0 or r.author.playtime_at_review < 0:
                valores_invalidos += 1

            if not r.recommendationid.strip():
                bloqueios.append("Encontrada review com recommendationid em branco.")

        if duplicados > 0:
            bloqueios.append(
                f"Detectadas {duplicados} duplicatas da chave (appid, recommendationid) no lote."
            )

        if valores_invalidos > 0:
            bloqueios.append(
                f"Detectados {valores_invalidos} registros com tempos de jogo negativos."
            )

        if inconsistencias_temporais > 0:
            avisos.append(
                f"Detectadas {inconsistencias_temporais} avaliações com timestamp_created maior que timestamp_updated."
            )

        aprovado = len(bloqueios) == 0

        return RelatorioQualidade(
            aprovado=aprovado,
            total_registros=len(reviews),
            total_duplicados=duplicados,
            total_inconsistencias_temporais=inconsistencias_temporais,
            total_valores_invalidos=valores_invalidos,
            mensagens_bloqueantes=tuple(bloqueios),
            avisos=tuple(avisos),
        )
