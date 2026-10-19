import numpy as np


class ExtratorBertimbau:
    """Extrai embeddings contextuais densos normalizados em L2 via Sentence-Transformers / BERTimbau."""

    def __init__(
        self,
        modelo_nome: str = "neuralmind/bert-base-portuguese-cased",
        dispositivo: str = "cpu",
        batch_size: int = 32,
        norma: str = "l2",
        modelo_precarregado: object | None = None,
    ) -> None:
        self._modelo_nome: str = modelo_nome
        self._dispositivo: str = dispositivo
        self._batch_size: int = batch_size
        self._norma: str = norma
        self._modelo_carregado: object | None = modelo_precarregado

    @property
    def modelo_nome(self) -> str:
        """Nome ou caminho do modelo Transformers."""
        return self._modelo_nome

    @property
    def dispositivo(self) -> str:
        """Dispositivo de processamento (cpu ou cuda)."""
        return self._dispositivo

    @property
    def batch_size(self) -> int:
        """Tamanho do lote para inferência."""
        return self._batch_size

    def _obter_modelo(self) -> object:
        """Carrega o modelo SentenceTransformer sob demanda (Lazy Loading)."""
        if self._modelo_carregado is None:
            from sentence_transformers import SentenceTransformer

            self._modelo_carregado = SentenceTransformer(
                self._modelo_nome,
                device=self._dispositivo,
            )
        return self._modelo_carregado

    def extrair_vetores(self, textos: list[str]) -> np.ndarray:
        """Gera matriz densa (N x D) de embeddings contextuais normalizados em L2."""
        if not textos:
            return np.empty((0, 0), dtype=np.float64)

        textos_processados = [t.strip() if t.strip() else "comentario" for t in textos]
        modelo = self._obter_modelo()

        encode_func = getattr(modelo, "encode", None)
        if callable(encode_func):
            vetores_brutos = encode_func(
                textos_processados,
                batch_size=self._batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            matriz = np.asarray(vetores_brutos, dtype=np.float64)
        else:
            dim = 768
            matriz = np.zeros((len(textos), dim), dtype=np.float64)

        if matriz.ndim == 1:
            matriz = np.expand_dims(matriz, axis=0)

        # Zera linhas correspondentes a textos vazios
        for idx, t in enumerate(textos):
            if not t.strip():
                matriz[idx] = 0.0

        # Normalização L2
        if self._norma:
            normas = np.linalg.norm(matriz, axis=1, keepdims=True)
            normas[normas == 0.0] = 1.0
            matriz = matriz / normas

        return matriz
