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

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed.

        Returns:
            List of floats representing the embedding vector.

        Raises:
            Exception: If embedding generation fails.
        """
        if not self._available or self.client is None:
            raise Exception("Gemini embedding model not properly configured")

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            response = self.client.models.embed_content(
                model=self.model_name,
                contents=text.strip(),
            )
            
            if not response or not response.embeddings:
                raise Exception("Invalid embedding response: no 'embeddings' field")
            
            first_embedding = response.embeddings[0]
            values = first_embedding.values if hasattr(first_embedding, "values") else first_embedding
            
            if not isinstance(values, (list, tuple)):
                raise Exception(f"Expected embedding to be list/tuple, got {type(values).__name__}")
            
            # Convert to float
            return [float(x) for x in values]
        
        except Exception as e:
            logger.error(f"Gemini embedding failed for text: {e}")
            raise Exception(f"Gemini embedding error: {str(e)}")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            Exception: If embedding generation fails.
        """
        if not self._available or self.client is None:
            raise Exception("Gemini embedding model not properly configured")

        if not texts:
            return []

        embeddings = []
        
        try:
            for text in texts:
                if text and text.strip():
                    embedding = self.embed_text(text)
                    embeddings.append(embedding)
                else:
                    # For empty texts, return zero vector
                    embeddings.append([0.0] * self._dimension)
            
            return embeddings
        
        except Exception as e:
            logger.error(f"Gemini batch embedding failed: {e}")
            raise Exception(f"Gemini batch embedding error: {str(e)}")

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
