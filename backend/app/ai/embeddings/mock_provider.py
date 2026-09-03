"""Mock Embedding Provider for testing without real API calls.

WARNING: These are hash-derived vectors with NO semantic meaning.
They are structurally valid floats but cosine similarity between them
reflects hash collisions, not topic similarity.

Use ONLY in unit tests where you need a fast, offline, deterministic
provider. NEVER use in production or for real semantic retrieval.
"""
import hashlib
from typing import List

from .base import EmbeddingProvider


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Test-only mock embedding provider.

    Generates deterministic hash-based vectors for structural tests.
    Not semantically meaningful — results of similarity search are arbitrary.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed_text(self, text: str) -> List[float]:
        """
        Generate mock embedding for a single text.

        Args:
            text: The text to embed.

        Returns:
            Deterministic embedding based on text hash.
        """
        # Create deterministic embeddings based on text hash
        hash_digest = hashlib.sha256(text.encode()).digest()
        
        # Convert hash bytes to float values in range [-1, 1]
        embedding = []
        for i in range(self.dimension):
            byte_val = hash_digest[i % len(hash_digest)]
            # Normalize to [-1, 1] range
            embedding.append((byte_val / 128.0) - 1.0)
        
        return embedding

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate mock embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of deterministic embeddings.
        """
        return [self.embed_text(text) for text in texts]

    def get_dimension(self) -> int:
        """
        Get the dimension of embedding vectors.

        Returns:
            Configured embedding dimension.
        """
        return self.dimension

    def is_available(self) -> bool:
        """
        Mock provider is always available.

        Returns:
            True, as mock provider doesn't require API keys.
        """
        return True
