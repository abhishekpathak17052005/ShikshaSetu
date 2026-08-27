"""LLM Provider Factory."""
from typing import Optional

from app.core.config import get_settings

from .base import LLMProvider
from .mock_provider import MockLLMProvider
from .openai_provider import OpenAIProvider


def get_llm_provider() -> LLMProvider:
    """
    Get the configured LLM provider based on settings.

    Returns:
        Configured LLM provider instance.

    Raises:
        ValueError: If provider is not recognized or not properly configured.
    """
    settings = get_settings()
    provider_name = settings.llm_provider.lower()

    if provider_name == "mock":
        return MockLLMProvider()
    elif provider_name == "openai":
        if not settings.llm_api_key:
            raise ValueError(
                "OpenAI provider selected but LLM_API_KEY not configured. "
                "Set LLM_API_KEY environment variable or use LLM_PROVIDER=mock for testing."
            )
        return OpenAIProvider(api_key=settings.llm_api_key, model=settings.llm_model)
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider_name}. "
            f"Supported: 'mock', 'openai'"
        )
