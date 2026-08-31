"""LLM Provider Factory."""
from typing import Optional

from app.core.config import Settings, get_settings

from .base import LLMProvider
from .mock_provider import MockLLMProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiLLMProvider


def get_llm_provider(settings: Optional[Settings] = None) -> LLMProvider:
    """
    Get the configured LLM provider based on settings.

    Returns:
        Configured LLM provider instance.

    Raises:
        ValueError: If provider is not recognized or not properly configured.
    """
    app_settings = settings or get_settings()
    provider_name = app_settings.llm_provider.lower()

    if provider_name == "mock":
        return MockLLMProvider()
    elif provider_name == "openai":
        if not settings.llm_api_key:
            raise ValueError(
                "OpenAI provider selected but LLM_API_KEY not configured. "
                "Set LLM_API_KEY environment variable or use LLM_PROVIDER=mock for testing."
            )
        return OpenAIProvider(api_key=settings.llm_api_key, model=settings.llm_model)
    elif provider_name == "gemini":
        if not settings.llm_api_key:
            raise ValueError(
                "Gemini provider selected but LLM_API_KEY not configured. "
                "Set LLM_API_KEY environment variable or use LLM_PROVIDER=mock for testing."
            )
        return GeminiLLMProvider(api_key=settings.llm_api_key, model=settings.llm_model)
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider_name}. "
            f"Supported: 'mock', 'openai', 'gemini'"
        )
