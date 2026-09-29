"""Google Gemini LLM Provider using the modern google.genai SDK — latency-optimised."""
import json
import logging
from typing import Optional

from google import genai
from google.genai import types

from .base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiLLMProvider(LLMProvider):
    """
    Google Gemini LLM provider implementation.

    Latency optimisations (2026-09-29):
      - system_instruction passed natively (not concatenated in prompt)
      - max_output_tokens capped at 350 for chat (was 1000)
      - Only 2 fallback models tried (was 5) — each retry adds 1-3s
      - temperature lowered to 0.3 (faster, more deterministic)
    """

    # Hard cap: never try more than 2 models for chat latency reasons
    _CHAT_FALLBACK = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]
    _JSON_FALLBACK = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model_name = model
        try:
            self.client = genai.Client(api_key=api_key)
            self._available = True
        except Exception as e:
            logger.error("Failed to initialize Gemini client for model %s: %s", model, e)
            self.client = None
            self._available = False

    def _models(self, fallbacks: list) -> list:
        """Deduplicated model list, capped at 2 entries."""
        seen: set = set()
        result: list = []
        for m in [self.model_name] + fallbacks:
            clean = m.replace("models/", "").strip()
            if clean and clean not in seen:
                seen.add(clean)
                result.append(clean)
                if len(result) == 2:
                    break
        return result

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Generate text using Gemini.

        Pass `system_instruction` to use Gemini's native system field (faster than
        prepending it to prompt). Cap max_output_tokens at 350 for chat speed.
        """
        if not self._available or self.client is None:
            raise Exception("Gemini model not properly configured")

        cfg_kwargs: dict = {
            "temperature": temperature,
            "max_output_tokens": max_tokens or 350,
        }
        if system_instruction:
            cfg_kwargs["system_instruction"] = system_instruction

        last_err = None
        for model in self._models(self._CHAT_FALLBACK):
            try:
                resp = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(**cfg_kwargs),
                )
                if resp and resp.text:
                    return resp.text
            except Exception as e:
                logger.warning("Gemini generate failed on %s: %s", model, e)
                last_err = e

        raise Exception(f"Gemini LLM error across all candidate models: {last_err}")

    def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
        system_instruction: Optional[str] = None,
    ):
        """Generate streaming text chunks using Gemini."""
        if not self._available or self.client is None:
            raise Exception("Gemini model not properly configured")

        cfg_kwargs: dict = {
            "temperature": temperature,
            "max_output_tokens": max_tokens or 350,
        }
        if system_instruction:
            cfg_kwargs["system_instruction"] = system_instruction

        try:
            stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**cfg_kwargs),
            )
            for chunk in stream:
                if chunk and chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error("Gemini streaming generation failed: %s", e)
            raise Exception(f"Gemini LLM streaming error: {e}")

    def generate_json(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
        schema: Optional[dict] = None,
        **kwargs,
    ):
        """Generate a JSON response using Gemini with resilient model fallback."""
        if not self._available or self.client is None:
            raise Exception("Gemini model not properly configured")

        json_prompt = prompt
        if "json" not in prompt.lower():
            json_prompt += "\n\nRespond with ONLY valid JSON, no markdown, no extra text."

        last_err = None
        for model in self._models(self._JSON_FALLBACK):
            try:
                resp = self.client.models.generate_content(
                    model=model,
                    contents=json_prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens or 4096,
                        response_mime_type="application/json",
                    ),
                )
                if not resp or not resp.text:
                    continue

                text = resp.text.strip()
                for prefix in ("```json", "```"):
                    if text.startswith(prefix):
                        text = text[len(prefix):]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

                result = json.loads(text)
                if isinstance(result, dict) and "questions" in result and isinstance(result["questions"], list):
                    return result["questions"]
                return result
            except Exception as e:
                logger.warning("Gemini JSON generation failed on %s: %s", model, e)
                last_err = e

        raise Exception(f"Gemini JSON generation failed on all candidate models. Last error: {last_err}")

    def is_available(self) -> bool:
        """Check if Gemini provider is available."""
        return self._available
