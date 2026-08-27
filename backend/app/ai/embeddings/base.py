"""Abstract Embedding Provider base class."""
from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.
    
    All embedding implementations must inherit from this class and implement
    the required abstract methods.
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """
        Get the dimension of embedding vectors.

        Returns:
            Dimension of the embedding vectors.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is properly configured and available.

        Returns:
            True if the provider can be used, False otherwise.
        """
        pass
