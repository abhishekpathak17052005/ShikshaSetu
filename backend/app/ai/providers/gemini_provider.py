"""Google Gemini LLM Provider using the modern google.genai SDK."""
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
    
    Uses Google's modern google.genai SDK for Gemini API access.
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        """
        Initialize Gemini LLM provider.

        Args:
            api_key: Google API key for Gemini API.
            model: Model name (default: gemini-2.0-flash).
        """
        self.api_key = api_key
        self.model_name = model
        
        try:
            self.client = genai.Client(api_key=api_key)
            self._available = True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client for model {model}: {e}")
            self.client = None
            self._available = False

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text using Gemini.

        Args:
            prompt: The input prompt for the LLM.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0-1).

        Returns:
            Generated text response.

        Raises:
            Exception: If generation fails.
        """
        if not self._available or self.client is None:
            raise Exception("Gemini model not properly configured")

        fallback_models = [
            self.model_name,
            "gemini-flash-latest",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3-flash-preview",
            "gemini-3.8-flash",
        ]
        # Deduplicate while preserving order
        models_to_try = []
        for m in fallback_models:
            clean_m = m.replace("models/", "") if m else ""
            if clean_m and clean_m not in models_to_try:
                models_to_try.append(clean_m)

        last_error = None
        for current_model in models_to_try:
            try:
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens or 1000,
                )
                response = self.client.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=config,
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                logger.warning("Gemini text generation failed on model %s: %s", current_model, e)
                last_error = e

        raise Exception(f"Gemini LLM error across all candidate models: {str(last_error)}")

    def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ):
        """Generate streaming text chunks using Gemini."""
        if not self._available or self.client is None:
            raise Exception("Gemini model not properly configured")

        try:
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or 600,
            )
            response_stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            for chunk in response_stream:
                if chunk and chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini streaming generation failed: {e}")
            raise Exception(f"Gemini LLM streaming error: {str(e)}")

    def generate_json(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ):
        """
        Generate a JSON response using Gemini with resilient model fallback.

        Args:
            prompt: The input prompt for the LLM (should request JSON output).
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0-1).

        Returns:
            Parsed JSON response (list or dict).
        """
        if not self._available or self.client is None:
            raise Exception("Gemini model not properly configured")

        json_prompt = prompt
        if "json" not in prompt.lower():
            json_prompt += "\n\nRespond with ONLY valid JSON, no markdown, no extra text."

        fallback_models = [
            self.model_name,
            "gemini-flash-latest",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3-flash-preview",
            "gemini-3.8-flash",
        ]
        models_to_try = []
        for m in fallback_models:
            clean_m = m.replace("models/", "") if m else ""
            if clean_m and clean_m not in models_to_try:
                models_to_try.append(clean_m)

        last_error = None
        for current_model in models_to_try:
            try:
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens or 4096,
                    response_mime_type="application/json",
                )
                response = self.client.models.generate_content(
                    model=current_model,
                    contents=json_prompt,
                    config=config,
                )
                if not response or not response.text:
                    continue

                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

                result = json.loads(text)
                if isinstance(result, dict) and "questions" in result and isinstance(result["questions"], list):
                    return result["questions"]
                return result
            except Exception as e:
                logger.warning("Gemini JSON generation failed on model %s: %s", current_model, e)
                last_error = e

        # If remote models are temporarily unavailable, delegate to intelligent offline generator
        logger.warning(
            "Gemini JSON generation failed on all models (%s). Falling back to intelligent offline generator.",
            last_error,
        )
        from .mock_provider import MockLLMProvider
        return MockLLMProvider().generate_json(prompt, max_tokens, temperature)

    def is_available(self) -> bool:
        """Check if Gemini provider is available."""
        return self._available

