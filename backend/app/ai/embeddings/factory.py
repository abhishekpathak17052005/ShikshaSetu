from typing import Optional
from app.core.config import Settings, get_settings

from .base import EmbeddingProvider
from .mock_provider import MockEmbeddingProvider
from .openai_provider import OpenAIEmbeddingProvider
from .gemini_provider import GeminiEmbeddingProvider


def get_embedding_provider(settings: Optional[Settings] = None) -> EmbeddingProvider:
    """
    Get the configured embedding provider based on settings.

    Returns:
        Configured embedding provider instance.

    Raises:
        ValueError: If provider is not recognized or not properly configured.
    """
    app_settings = settings or get_settings()
    provider_name = app_settings.embedding_provider.lower()

    if provider_name == "mock":
        return MockEmbeddingProvider(dimension=app_settings.embedding_dimension)
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
    elif provider_name == "gemini":
        if not settings.llm_api_key:
            raise ValueError(
                "Gemini embedding provider selected but LLM_API_KEY not configured. "
                "Set LLM_API_KEY environment variable or use EMBEDDING_PROVIDER=mock for testing."
            )
        return GeminiEmbeddingProvider(
            api_key=settings.llm_api_key,
            model=settings.embedding_model,
            dimension=settings.embedding_dimension,
        )
    else:
        raise ValueError(
            f"Unknown embedding provider: {provider_name}. "
            f"Supported: 'mock', 'openai', 'gemini'"
        )
