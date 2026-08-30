"""Google Gemini Embedding Provider."""
import logging
from typing import List

import google.generativeai as genai

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Google Gemini embedding provider implementation.
    
    Uses Google's official generativeai SDK for text embeddings.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "models/embedding-001",
        dimension: int = 768,
    ):
        """
        Initialize Gemini embedding provider.

        Args:
            api_key: Google API key for Gemini API.
            model: Model name for embeddings (default: models/embedding-001).
            dimension: Expected embedding dimension (default: 768 for embedding-001).
        """
        self.api_key = api_key
        self.model_name = model
        self._dimension = dimension
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        try:
            # Test the model by embedding a simple text
            self._test_embedding()
            self._available = True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini embedding model {model}: {e}")
            self._available = False

    def _test_embedding(self) -> None:
        """Test that embedding model is working."""
        try:
            result = genai.embed_content(
                model=self.model_name,
                content="test"
            )
            if "embedding" not in result:
                raise Exception("Invalid embedding response format")
            # Update dimension based on actual response
            if "embedding" in result:
                self._dimension = len(result["embedding"])
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
        if not self._available:
            raise Exception("Gemini embedding model not properly configured")

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text.strip()
            )
            
            if "embedding" not in result:
                raise Exception("Invalid embedding response: no 'embedding' field")
            
            embedding = result["embedding"]
            
            if not isinstance(embedding, list):
                raise Exception(f"Expected embedding to be list, got {type(embedding).__name__}")
            
            # Convert to float if needed
            return [float(x) for x in embedding]
        
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
        if not self._available:
            raise Exception("Gemini embedding model not properly configured")

        if not texts:
            return []

        embeddings = []
        
        try:
            # Gemini API prefers to embed texts one at a time or in small batches
            # We'll embed one at a time for reliability
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
