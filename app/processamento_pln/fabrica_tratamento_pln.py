"""Fábrica para instanciar estratégias de tratamento de linguagem natural (GoF Factory)."""

from typing import ClassVar

from app.conf_yaml import ConfigPLNInfo
from app.excecoes import ErroPreprocessamento
from app.processamento_pln.estrategia_count import EstrategiaTratamentoCount
from app.processamento_pln.estrategia_spacy import EstrategiaTratamentoSpacy
from app.processamento_pln.estrategia_tfidf import EstrategiaTratamentoTFIDF
from app.processamento_pln.estrategia_tratamento_base import ProtocoloTratamentoTexto


class FabricaTratamentoPLN:
    """Instancia estratégias de pré-processamento e vetorização de texto baseadas em YAML."""

    _registro: ClassVar[dict[str, type[ProtocoloTratamentoTexto]]] = {
        "spacy": EstrategiaTratamentoSpacy,
        "tfidf": EstrategiaTratamentoTFIDF,
        "count": EstrategiaTratamentoCount,
    }

    @classmethod
    def registrar_estrategia(
        cls,
        nome_tratamento: str,
        classe_estrategia: type[ProtocoloTratamentoTexto],
    ) -> None:
        """Permite estender a fábrica com novos tratamentos em runtime."""
        cls._registro[nome_tratamento.lower()] = classe_estrategia

    @classmethod
    def criar_estrategia(cls, config: ConfigPLNInfo) -> ProtocoloTratamentoTexto:
        """Cria e injeta as configurações na estratégia selecionada no YAML."""
        tratamento = config.tratamento.lower()
        match tratamento:
            case "spacy":
                return EstrategiaTratamentoSpacy(config.spacy)
            case "tfidf":
                return EstrategiaTratamentoTFIDF(config.tfidf)
            case "count":
                return EstrategiaTratamentoCount(config.count)
            case outro if outro in cls._registro:
                return cls._registro[outro]()
            case tratamento_invalido:
                opcoes = list(cls._registro.keys())
                raise ErroPreprocessamento(
                    f"Tratamento de PLN '{tratamento_invalido}' não suportado. Opções válidas: {opcoes}"
                )
