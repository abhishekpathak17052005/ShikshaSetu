"""
FallbackLLMProvider — transparent Gemini → Groq → Mock cascade.

When Gemini raises any exception (quota exceeded, server error, rate-limit,
model unavailable…) this wrapper automatically retries the same call against
the Groq provider.  If Groq also fails it falls through to the local
offline MockLLMProvider so the system always returns *something*.

Usage (handled automatically by the factory):
    provider = FallbackLLMProvider(primary=gemini, secondary=groq)
"""
import logging
from typing import Generator, Optional

from .base import LLMProvider

logger = logging.getLogger(__name__)

# Groq-specific error keywords that indicate a transient / quota failure
_FALLBACK_KEYWORDS = (
    "quota",
    "rate limit",
    "rate_limit",
    "exceeded",
    "overloaded",
    "unavailable",
    "server error",
    "500",
    "503",
    "502",
    "timeout",
    "resource_exhausted",
    "RESOURCE_EXHAUSTED",
    "429",
    "insufficient_quota",
)


def _should_fallback(exc: Exception) -> bool:
    """Heuristic: decide whether to try the next provider or re-raise immediately."""
    msg = str(exc).lower()
    return any(kw.lower() in msg for kw in _FALLBACK_KEYWORDS) or True
    # NOTE: we always fall back on *any* Gemini error so we never leave the
    # user hanging.  Remove `or True` if you want stricter behaviour.


class FallbackLLMProvider(LLMProvider):
    """
    Cascading LLM provider: primary (Gemini) → secondary (Groq) → offline mock.

    All three `generate*` methods follow the same pattern:
      1. Try primary.
      2. On failure log a warning and try secondary.
      3. On secondary failure log an error and try offline mock.
      4. Re-raise only if all three fail.
    """

    def __init__(self, primary: LLMProvider, secondary: LLMProvider):
        self._primary = primary
        self._secondary = secondary
        self._mock: Optional[LLMProvider] = None  # lazy-loaded

    def _get_mock(self) -> LLMProvider:
        if self._mock is None:
            from .mock_provider import MockLLMProvider
            self._mock = MockLLMProvider()
        return self._mock

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        # 1. Try Gemini
        try:
            result = self._primary.generate(prompt, max_tokens=max_tokens, temperature=temperature)
            if result:
                return result
        except Exception as exc:
            logger.warning(
                "Primary LLM (Gemini) generate failed — falling back to Groq. Reason: %s", exc
            )

        # 2. Try Groq
        try:
            result = self._secondary.generate(prompt, max_tokens=max_tokens, temperature=temperature)
            if result:
                logger.info("Groq fallback generate succeeded.")
                return result
        except Exception as exc:
            logger.error(
                "Secondary LLM (Groq) generate also failed — using offline mock. Reason: %s", exc
            )

        # 3. Offline mock (always returns something meaningful)
        return self._get_mock().generate(prompt, max_tokens=max_tokens, temperature=temperature)

    def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """
        Streaming fallback cascade.

        Gemini streaming is attempted first; if it raises before or during
        streaming we collect the full Groq response and yield it as one chunk.
        """
        # 1. Try Gemini stream
        try:
            chunks = list(self._primary.generate_stream(prompt, max_tokens=max_tokens, temperature=temperature))
            if chunks:
                yield from chunks
                return
        except Exception as exc:
            logger.warning(
                "Primary LLM (Gemini) stream failed — falling back to Groq. Reason: %s", exc
            )

        # 2. Try Groq stream
        try:
            if hasattr(self._secondary, "generate_stream"):
                chunks = list(self._secondary.generate_stream(prompt, max_tokens=max_tokens, temperature=temperature))
                if chunks:
                    logger.info("Groq fallback stream succeeded.")
                    yield from chunks
                    return
        except Exception as exc:
            logger.error(
                "Secondary LLM (Groq) stream failed — using offline mock. Reason: %s", exc
            )

        # 3. Offline mock — yield single chunk
        text = self._get_mock().generate(prompt, max_tokens=max_tokens, temperature=temperature)
        yield text

    def generate_json(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        schema: Optional[dict] = None,
        **kwargs,
    ):
        # 1. Try Gemini
        try:
            result = self._primary.generate_json(
                prompt, max_tokens=max_tokens, temperature=temperature, schema=schema, **kwargs
            )
            if result is not None:
                return result
        except Exception as exc:
            logger.warning(
                "Primary LLM (Gemini) generate_json failed — falling back to Groq. Reason: %s", exc
            )

        # 2. Try Groq
        try:
            result = self._secondary.generate_json(
                prompt, max_tokens=max_tokens, temperature=temperature, schema=schema, **kwargs
            )
            if result is not None:
                logger.info("Groq fallback generate_json succeeded.")
                return result
        except Exception as exc:
            logger.error(
                "Secondary LLM (Groq) generate_json also failed — using offline mock. Reason: %s", exc
            )

        # 3. Offline mock
        return self._get_mock().generate_json(prompt, max_tokens=max_tokens, temperature=temperature)

    def is_available(self) -> bool:
        return self._primary.is_available() or self._secondary.is_available()
