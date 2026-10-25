"""Pacote raiz da aplicação Steam Reviews Clustering."""

from app.fachada_pipeline import FachadaPipelineClustering, ResultadoExecucaoPipeline

__version__ = "0.1.0"

__all__ = [
    "FachadaPipelineClustering",
    "ResultadoExecucaoPipeline",
    "__version__",
]
