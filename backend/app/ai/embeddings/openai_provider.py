"""OpenAI Embedding Provider for real API calls."""
from typing import List

from openai import OpenAI, APIError, RateLimitError

from .base import EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    Real OpenAI embedding provider.
    
    Uses the OpenAI API to generate text embeddings.
    Requires LLM_API_KEY environment variable.
    """

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embedding provider.

        Args:
            api_key: OpenAI API key.
            model: Model name (e.g., "text-embedding-3-small", "text-embedding-3-large").
        """
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self._dimension = None

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using OpenAI API.

        Args:
            text: The text to embed.

        Returns:
            Embedding vector.

        Raises:
            APIError: If API call fails.
        """
        embeddings = self.embed_texts([text])
        return embeddings[0]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using OpenAI API.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            APIError: If API call fails.
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
            )
            
            # Store dimension from first embedding if not already known
            if self._dimension is None and response.data:
                self._dimension = len(response.data[0].embedding)
            
            # Return embeddings in order
            return [item.embedding for item in response.data]
        except (APIError, RateLimitError) as e:
            raise Exception(f"OpenAI embedding API error: {str(e)}")

    def get_dimension(self) -> int:
        """
        Get the dimension of embedding vectors.

        Returns:
            Dimension of the embedding vectors.
            For text-embedding-3-small: 1536
            For text-embedding-3-large: 3072
        """
        # Standard dimensions for OpenAI embedding models
        if "small" in self.model.lower():
            return 1536
        elif "large" in self.model.lower():
            return 3072
        else:
            # Fallback: return the cached dimension if available
            return self._dimension or 1536

    def is_available(self) -> bool:
        """
        Check if OpenAI embedding provider is properly configured.

        Returns:
            True if API key is present and valid.
        """
        return bool(self.api_key and self.api_key.strip())
