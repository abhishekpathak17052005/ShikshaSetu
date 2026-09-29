"""Groq LLM Provider — fallback for when Gemini is unavailable."""
import json
import logging
from typing import Generator, Optional

from groq import Groq, APIStatusError, APITimeoutError, APIConnectionError

from .base import LLMProvider

logger = logging.getLogger(__name__)

# Ordered list of Groq models to try (fastest / cheapest first)
_GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]


class GroqLLMProvider(LLMProvider):
    """
    Groq LLM provider — used as a fallback when Gemini is unavailable.

    Wraps the official `groq` Python SDK and implements the same LLMProvider
    interface so it can be dropped in transparently.
    """

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the Groq provider.

        Args:
            api_key: Groq API key (from https://console.groq.com).
            model:   Primary model to try first.
        """
        self.api_key = api_key
        self.model_name = model

        try:
            self.client = Groq(api_key=api_key)
            self._available = True
            logger.info("GroqLLMProvider initialised (primary model: %s)", model)
        except Exception as exc:
            logger.error("Failed to initialise Groq client: %s", exc)
            self.client = None
            self._available = False

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _models_to_try(self) -> list[str]:
        """Return a deduplicated ordered list of models starting with the configured one."""
        seen: set[str] = set()
        result: list[str] = []
        for m in [self.model_name, *_GROQ_MODELS]:
            if m and m not in seen:
                seen.add(m)
                result.append(m)
        return result

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text using Groq.

        Tries each model in _models_to_try() in order.  Raises only after
        all candidates are exhausted.
        """
        if not self._available or self.client is None:
            raise Exception("Groq provider is not properly configured (missing or invalid API key).")

        last_error: Optional[Exception] = None
        for model in self._models_to_try():
            try:
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens or 1000,
                    temperature=temperature,
                )
                text = completion.choices[0].message.content
                if text:
                    logger.debug("Groq text generation succeeded on model %s", model)
                    return text
            except (APIStatusError, APITimeoutError, APIConnectionError) as exc:
                logger.warning("Groq text generation failed on model %s: %s", model, exc)
                last_error = exc
            except Exception as exc:
                logger.warning("Groq text generation unexpected error on model %s: %s", model, exc)
                last_error = exc

        raise Exception(f"Groq LLM error across all candidate models: {last_error}")

    def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Generate streaming text chunks using Groq."""
        if not self._available or self.client is None:
            raise Exception("Groq provider is not properly configured.")

        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens or 600,
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    def generate_json(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        schema: Optional[dict] = None,
        **kwargs,
    ):
        """
        Generate a JSON response using Groq.

        Adds a JSON-enforcement suffix to the prompt and parses the response.
        Falls back gracefully across multiple models before raising.
        """
        if not self._available or self.client is None:
            raise Exception("Groq provider is not properly configured.")

        json_prompt = prompt
        if "json" not in prompt.lower():
            json_prompt += "\n\nRespond with ONLY valid JSON, no markdown, no extra text."

        last_error: Optional[Exception] = None
        for model in self._models_to_try():
            try:
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": json_prompt}],
                    max_tokens=max_tokens or 4096,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
                text = (completion.choices[0].message.content or "").strip()

                # Strip markdown fences if present
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

                result = json.loads(text)
                # Unwrap {"questions": [...]} envelope if present
                if isinstance(result, dict) and "questions" in result and isinstance(result["questions"], list):
                    return result["questions"]
                logger.debug("Groq JSON generation succeeded on model %s", model)
                return result
            except Exception as exc:
                logger.warning("Groq JSON generation failed on model %s: %s", model, exc)
                last_error = exc

        raise Exception(f"Groq JSON generation failed across all models: {last_error}")

    def is_available(self) -> bool:
        """Return True if the Groq client is initialised."""
        return self._available
