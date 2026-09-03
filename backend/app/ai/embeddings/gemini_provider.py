"""Google Gemini Embedding Provider using the modern google.genai SDK."""
import logging
from typing import List

from google import genai
from google.genai import types

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Google Gemini embedding provider implementation.
    
    Uses Google's modern google.genai SDK for text embeddings.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-004",
        dimension: int = 768,
    ):
        """
        Initialize Gemini embedding provider.

        Args:
            api_key: Google API key for Gemini API.
            model: Model name for embeddings (default: text-embedding-004).
            dimension: Expected embedding dimension (default: 768 for text-embedding-004).
        """
        self.api_key = api_key
        self.model_name = model
        self._dimension = dimension
        
        try:
            self.client = genai.Client(api_key=api_key)
            self._test_embedding()
            self._available = True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini embedding model {model}: {e}")
            self.client = None
            self._available = False

    def _test_embedding(self) -> None:
        """Test that embedding model is working."""
        try:
            if not self.client:
                raise Exception("Client not initialized")
            response = self.client.models.embed_content(
                model=self.model_name,
                contents="test",
            )
            if not response or not response.embeddings:
                raise Exception("Invalid embedding response format")
            if response.embeddings and hasattr(response.embeddings[0], "values"):
                self._dimension = len(response.embeddings[0].values)
        except Exception as e:
            raise Exception(f"Embedding model test failed: {str(e)}")

    # REMOVED: _fallback_embedding (SHA-256 hash vectors)
    # Hash-derived vectors have no semantic meaning and produce random cosine
    # similarities. Callers must handle EmbeddingUnavailableError and mark the
    # chunk as embedding_status=FAILED for honest retry instead of silently
    # substituting meaningless vectors.

    def embed_text(self, text: str) -> List[float]:
        """
        Generate a real semantic embedding for text.

        Raises:
            Exception: If the API call fails. Callers should catch this and
                       set embedding_status=FAILED on the affected chunk rather
                       than using a hash-based fallback.
        """
        if not text or not text.strip():
            return [0.0] * self._dimension

        if not self._available or self.client is None:
            raise Exception(
                "Gemini embedding provider is not available "
                "(API key missing or initialization failed). "
                "Chunk will be marked FAILED for retry."
            )

        response = self.client.models.embed_content(
            model=self.model_name,
            contents=text.strip(),
        )

        if not response or not response.embeddings:
            raise Exception("Gemini returned empty embedding response")

        first_embedding = response.embeddings[0]
        values = (
            first_embedding.values
            if hasattr(first_embedding, "values")
            else first_embedding
        )

        if not isinstance(values, (list, tuple)):
            raise Exception(f"Unexpected embedding format: {type(values)}")

        return [float(x) for x in values]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        Raises on any individual failure — callers should iterate and handle
        per-chunk failures via embed_and_persist_chunks() in rag/embedding_index.py.
        """
        if not texts:
            return []
        return [self.embed_text(t) for t in texts]

    def get_dimension(self) -> int:
        """
        Get the dimension of embedding vectors.

        Returns:
            Dimension of the embedding vectors.
        """
        return self._dimension

    def is_available(self) -> bool:
        """
        Check if Gemini embedding provider is available.

        Returns:
            True if provider is configured and accessible.
        """
        return self._available
