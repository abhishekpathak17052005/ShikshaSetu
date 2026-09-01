"""LLM Provider Factory."""
import os
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
    gemini_key = app_settings.llm_api_key or os.environ.get("GEMINI_API_KEY", "") or os.environ.get("LLM_API_KEY", "")
    openai_key = app_settings.llm_api_key or os.environ.get("OPENAI_API_KEY", "") or os.environ.get("LLM_API_KEY", "")

    if provider_name == "mock":
        return MockLLMProvider()
    elif provider_name == "openai":
        if not openai_key:
            return MockLLMProvider()
        return OpenAIProvider(api_key=openai_key, model=app_settings.llm_model)
    elif provider_name == "gemini":
        if not gemini_key:
            return MockLLMProvider()
        return GeminiLLMProvider(api_key=gemini_key, model=app_settings.llm_model)
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider_name}. "
            f"Supported: 'mock', 'openai', 'gemini'"
        )

