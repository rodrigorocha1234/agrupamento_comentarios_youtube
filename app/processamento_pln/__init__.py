"""Módulo de Processamento de Linguagem Natural (PLN) baseado em padrões GoF."""

from app.processamento_pln.adaptador_matriz import AdaptadorMatrizPLN
from app.processamento_pln.estrategia_count import EstrategiaTratamentoCount
from app.processamento_pln.estrategia_spacy import EstrategiaTratamentoSpacy
from app.processamento_pln.estrategia_tfidf import EstrategiaTratamentoTFIDF
from app.processamento_pln.estrategia_tratamento_base import ProtocoloTratamentoTexto
from app.processamento_pln.fabrica_tratamento_pln import FabricaTratamentoPLN
from app.processamento_pln.fachada_pln import FachadaProcessamentoPLN

__all__ = [
    "AdaptadorMatrizPLN",
    "EstrategiaTratamentoCount",
    "EstrategiaTratamentoSpacy",
    "EstrategiaTratamentoTFIDF",
    "FabricaTratamentoPLN",
    "FachadaProcessamentoPLN",
    "ProtocoloTratamentoTexto",
]
