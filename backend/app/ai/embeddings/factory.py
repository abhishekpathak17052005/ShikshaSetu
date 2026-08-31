import os
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
    gemini_key = app_settings.llm_api_key or os.environ.get("GEMINI_API_KEY", "") or os.environ.get("LLM_API_KEY", "")

    if provider_name == "mock":
        return MockEmbeddingProvider(dimension=app_settings.embedding_dimension)
    elif provider_name == "openai":
        if not app_settings.llm_api_key:
            return MockEmbeddingProvider(dimension=app_settings.embedding_dimension)
        return OpenAIEmbeddingProvider(
            api_key=app_settings.llm_api_key,
            model=app_settings.embedding_model,
        )
    elif provider_name == "gemini":
        if not gemini_key:
            return MockEmbeddingProvider(dimension=app_settings.embedding_dimension)
        return GeminiEmbeddingProvider(
            api_key=gemini_key,
            model=app_settings.embedding_model,
            dimension=app_settings.embedding_dimension,
        )
    else:
        return MockEmbeddingProvider(dimension=app_settings.embedding_dimension)
