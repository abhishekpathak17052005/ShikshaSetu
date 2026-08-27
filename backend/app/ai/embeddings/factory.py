"""Embedding Provider Factory."""
from app.core.config import get_settings

from .base import EmbeddingProvider
from .mock_provider import MockEmbeddingProvider
from .openai_provider import OpenAIEmbeddingProvider


def get_embedding_provider() -> EmbeddingProvider:
    """
    Get the configured embedding provider based on settings.

    Returns:
        Configured embedding provider instance.

    Raises:
        ValueError: If provider is not recognized or not properly configured.
    """
    settings = get_settings()
    provider_name = settings.embedding_provider.lower()

    if provider_name == "mock":
        return MockEmbeddingProvider(dimension=settings.embedding_dimension)
    elif provider_name == "openai":
        if not settings.llm_api_key:
            raise ValueError(
                "OpenAI embedding provider selected but LLM_API_KEY not configured. "
                "Set LLM_API_KEY environment variable or use EMBEDDING_PROVIDER=mock for testing."
            )
        return OpenAIEmbeddingProvider(
            api_key=settings.llm_api_key,
            model=settings.embedding_model,
        )
    else:
        raise ValueError(
            f"Unknown embedding provider: {provider_name}. "
            f"Supported: 'mock', 'openai'"
        )
