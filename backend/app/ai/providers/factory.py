"""LLM Provider Factory — with Gemini → Groq automatic fallback."""
import logging
import os
from typing import Optional

from app.core.config import Settings, get_settings

from .base import LLMProvider
from .mock_provider import MockLLMProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiLLMProvider
from .groq_provider import GroqLLMProvider
from .fallback_provider import FallbackLLMProvider

logger = logging.getLogger(__name__)


def get_llm_provider(settings: Optional[Settings] = None) -> LLMProvider:
    """
    Return the configured LLM provider.

    When LLM_PROVIDER=gemini **and** a GROQ_API_KEY is available, the
    returned provider is a FallbackLLMProvider that transparently tries
    Gemini first and automatically retries on Groq when Gemini fails
    (quota exceeded, server down, rate-limited, etc.).

    Provider resolution order:
        mock   → MockLLMProvider  (offline, always works)
        openai → OpenAIProvider
        gemini → FallbackLLMProvider(Gemini, Groq) if GROQ_API_KEY present
                 GeminiLLMProvider                 otherwise
        groq   → GroqLLMProvider  (primary = Groq, no Gemini)

    Raises:
        ValueError: If LLM_PROVIDER is not one of the supported values.
    """
    app_settings = settings or get_settings()
    provider_name = app_settings.llm_provider.lower()

    gemini_key = (
        app_settings.llm_api_key
        or os.environ.get("GEMINI_API_KEY", "")
        or os.environ.get("LLM_API_KEY", "")
    )
    openai_key = (
        app_settings.llm_api_key
        or os.environ.get("OPENAI_API_KEY", "")
        or os.environ.get("LLM_API_KEY", "")
    )
    groq_key = os.environ.get("GROQ_API_KEY", "") or getattr(app_settings, "groq_api_key", "")

    if provider_name == "mock":
        return MockLLMProvider()

    elif provider_name == "openai":
        if not openai_key:
            logger.warning("LLM_PROVIDER=openai but no API key found — using MockLLMProvider.")
            return MockLLMProvider()
        return OpenAIProvider(api_key=openai_key, model=app_settings.llm_model)

    elif provider_name == "gemini":
        if not gemini_key:
            logger.warning("LLM_PROVIDER=gemini but no Gemini API key found — using MockLLMProvider.")
            return MockLLMProvider()

        gemini_provider = GeminiLLMProvider(api_key=gemini_key, model=app_settings.llm_model)

        if groq_key:
            groq_provider = GroqLLMProvider(api_key=groq_key)
            if groq_provider.is_available():
                logger.info(
                    "LLM_PROVIDER=gemini: Groq fallback enabled. "
                    "Requests will cascade Gemini → Groq → Offline-Mock on failure."
                )
                return FallbackLLMProvider(primary=gemini_provider, secondary=groq_provider)
            else:
                logger.warning(
                    "LLM_PROVIDER=gemini: GROQ_API_KEY set but Groq provider unavailable. "
                    "Running Gemini only (no Groq fallback)."
                )
                return gemini_provider
        else:
            logger.info(
                "LLM_PROVIDER=gemini: No GROQ_API_KEY set — running Gemini only (no Groq fallback). "
                "Set GROQ_API_KEY in .env to enable automatic failover."
            )
            return gemini_provider

    elif provider_name == "groq":
        if not groq_key:
            logger.warning("LLM_PROVIDER=groq but no GROQ_API_KEY found — using MockLLMProvider.")
            return MockLLMProvider()
        groq_provider = GroqLLMProvider(api_key=groq_key, model=app_settings.llm_model)
        if not groq_provider.is_available():
            logger.warning("LLM_PROVIDER=groq but Groq provider is unavailable — using MockLLMProvider.")
            return MockLLMProvider()
        return groq_provider

    else:
        raise ValueError(
            f"Unknown LLM provider: {provider_name!r}. "
            "Supported values: 'mock', 'openai', 'gemini', 'groq'"
        )
