from collections.abc import Callable
from typing import Final, Literal, final

from app.agrupamento_modelos.agrupador_dbscan import AgrupadorDbscan
from app.agrupamento_modelos.agrupador_hdbscan import AgrupadorHdbscan
from app.agrupamento_modelos.agrupador_kmeans import AgrupadorKMeans
from app.agrupamento_modelos.capacidades_algoritmo import EstrategiaAgrupamento
from app.dominio_contratos.modelos_dados import TipoParametroAlgoritmo

TipoCriadorAgrupador = Callable[[dict[str, TipoParametroAlgoritmo]], EstrategiaAgrupamento]


class ErroAlgoritmoNaoRegistrado(Exception):
    """Exceção levantada quando um algoritmo não estiver no catálogo de registros."""


def _extrair_int(valor: TipoParametroAlgoritmo, padrao: int) -> int:
    if valor is None:
        return padrao
    try:
        return int(str(valor))
    except (ValueError, TypeError):
        return padrao


def _extrair_float(valor: TipoParametroAlgoritmo, padrao: float) -> float:
    if valor is None:
        return padrao
    try:
        return float(str(valor))
    except (ValueError, TypeError):
        return padrao


@final
class FabricaAgrupadores:
    """Registry e Factory para criação desacoplada de estratégias de clustering."""

    def __init__(self) -> None:
        self._registro: Final[dict[str, TipoCriadorAgrupador]] = {}
        self._registrar_padroes()

    def registrar_algoritmo(self, nome: str, criador: TipoCriadorAgrupador) -> None:
        """Registra uma nova estratégia de agrupamento."""
        self._registro[nome.lower()] = criador

    def criar_agrupador(
        self, nome_algoritmo: str, parametros: dict[str, TipoParametroAlgoritmo] | None = None
    ) -> EstrategiaAgrupamento:
        """Instancia o algoritmo correspondente sem condicionais no domínio."""
        chave = nome_algoritmo.lower()
        criador = self._registro.get(chave)
        if criador is None:
            raise ErroAlgoritmoNaoRegistrado(
                f"Algoritmo de clustering '{nome_algoritmo}' não suportado. Opções registradas: {list(self._registro.keys())}"
            )
        return criador(parametros or {})

    def _registrar_padroes(self) -> None:
        """Registra KMeans, DBSCAN e HDBSCAN."""

        def _criar_kmeans(params: dict[str, TipoParametroAlgoritmo]) -> EstrategiaAgrupamento:
            n_clusters = _extrair_int(params.get("n_clusters"), 4)
            random_state = _extrair_int(params.get("random_state"), 42)
            val_init = params.get("n_init", 10)
            n_init: int | Literal["auto"] = (
                "auto"
                if str(val_init).lower() == "auto"
                else _extrair_int(val_init, 10)
            )
            return AgrupadorKMeans(
                n_clusters=n_clusters, random_state=random_state, n_init=n_init
            )

        def _criar_dbscan(params: dict[str, TipoParametroAlgoritmo]) -> EstrategiaAgrupamento:
            eps = _extrair_float(params.get("eps"), 0.5)
            min_samples = _extrair_int(params.get("min_samples"), 5)
            return AgrupadorDbscan(eps=eps, min_samples=min_samples)

        def _criar_hdbscan(params: dict[str, TipoParametroAlgoritmo]) -> EstrategiaAgrupamento:
            min_cluster_size = _extrair_int(params.get("min_cluster_size"), 20)
            min_samples = _extrair_int(params.get("min_samples"), 5)
            return AgrupadorHdbscan(
                min_cluster_size=min_cluster_size, min_samples=min_samples
            )

        self.registrar_algoritmo("kmeans", _criar_kmeans)
        self.registrar_algoritmo("dbscan", _criar_dbscan)
        self.registrar_algoritmo("hdbscan", _criar_hdbscan)
