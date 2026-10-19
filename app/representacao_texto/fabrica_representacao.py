from typing import Protocol, runtime_checkable
import numpy as np
from scipy.sparse import csr_matrix

from app.configuracao_geral.modelos_configuracao import (
    ConfiguracaoProcessamento,
)
from app.representacao_texto.extrator_bertimbau import ExtratorBertimbau
from app.representacao_texto.extrator_embeddings import ExtratorEmbeddings
from app.representacao_texto.redutor_dimensionalidade import (
    RedutorDimensionalidade,
)
from app.representacao_texto.redutor_umap import RedutorUmap
from app.representacao_texto.vetorizador_tfidf import VetorizadorTfidf


@runtime_checkable
class ProtocoloRedutor(Protocol):
    """Protocolo estrutural para redutores de dimensionalidade."""

    def ajustar_e_reduzir(self, matriz: csr_matrix | np.ndarray) -> np.ndarray: ...
    def reduzir(self, matriz: csr_matrix | np.ndarray) -> np.ndarray: ...


class FabricaRepresentacao:
    """Instancia o vetorizador TF-IDF e o redutor dimensional com base nas configurações."""

    @staticmethod
    def criar_vetorizador(config: ConfiguracaoProcessamento) -> VetorizadorTfidf:
        """Instancia o VetorizadorTfidf a partir da configuração de representação."""
        return VetorizadorTfidf(
            min_df=config.representacao.min_df,
            max_df=config.representacao.max_df,
            ngram_range=config.representacao.ngram_range,
            sublinear_tf=config.representacao.sublinear_tf,
            norma=config.representacao.norma,
        )

    @staticmethod
    def criar_redutor_opcional(
        config: ConfiguracaoProcessamento,
    ) -> ProtocoloRedutor | None:
        """Instancia o redutor dimensional (UMAP ou SVD) caso habilitado nas configurações."""
        if not config.reducao.ativa:
            return None
        if config.reducao.tecnica.lower() == "umap":
            return RedutorUmap(
                componentes=config.reducao.componentes,
                n_vizinhos=config.reducao.n_vizinhos,
                distancia_minima=config.reducao.distancia_minima,
                metrica=config.reducao.metrica,
                random_state=config.reducao.random_state,
                norma=None,
            )
        return RedutorDimensionalidade(
            componentes=config.reducao.componentes,
        )

    @staticmethod
    def criar_redutor_umap(
        config: ConfiguracaoProcessamento,
    ) -> RedutorUmap:
        """Instancia diretamente o RedutorUmap configurado."""
        return RedutorUmap(
            componentes=config.reducao.componentes,
            n_vizinhos=config.reducao.n_vizinhos,
            distancia_minima=config.reducao.distancia_minima,
            metrica=config.reducao.metrica,
            random_state=config.reducao.random_state,
            norma=None,
        )

    @staticmethod
    def criar_extrator_embeddings(
        config: ConfiguracaoProcessamento,
    ) -> ExtratorEmbeddings:
        """Instancia o ExtratorEmbeddings configurado com o modelo spaCy do pipeline."""
        return ExtratorEmbeddings(
            modelo_nome=config.spacy_modelo,
            norma=config.representacao.norma,
        )

    @staticmethod
    def criar_extrator_bertimbau(
        config: ConfiguracaoProcessamento,
    ) -> ExtratorBertimbau:
        """Instancia o ExtratorBertimbau configurado com Sentence-Transformers."""
        return ExtratorBertimbau(
            modelo_nome=config.representacao.modelo_transformers,
            dispositivo=config.representacao.dispositivo_transformers,
            batch_size=config.representacao.batch_size_transformers,
            norma=config.representacao.norma,
        )


