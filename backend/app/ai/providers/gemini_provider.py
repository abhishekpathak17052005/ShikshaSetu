"""Google Gemini LLM Provider."""
import json
import logging
from typing import Optional

import google.generativeai as genai

from .base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiLLMProvider(LLMProvider):
    """
    Google Gemini LLM provider implementation.
    
    Uses Google's official generativeai SDK for Gemini API access.
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
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        try:
            self.model = genai.GenerativeModel(model_name=model)
            self._available = True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model {model}: {e}")
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
        if not self._available:
            raise Exception("Gemini model not properly configured")

        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or 1000,
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
            )
            
            if not response or not response.text:
                raise Exception("Gemini returned empty response")
            
            return response.text
        
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise Exception(f"Gemini LLM error: {str(e)}")

    def generate_json(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> dict:
        """
        Generate a JSON response using Gemini.

        Args:
            prompt: The input prompt for the LLM (should request JSON output).
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0-1).

        Returns:
            Parsed JSON response as dictionary.

        Raises:
            Exception: If generation or JSON parsing fails.
        """
        if not self._available:
            raise Exception("Gemini model not properly configured")

        try:
            # Add explicit instruction to output valid JSON
            json_prompt = prompt
            if "json" not in prompt.lower():
                json_prompt += "\n\nRespond with ONLY valid JSON, no markdown, no extra text."
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or 2000,
            )
            
            response = self.model.generate_content(
                json_prompt,
                generation_config=generation_config,
            )
            
            if not response or not response.text:
                raise Exception("Gemini returned empty response")
            
            # Try to parse response as JSON
            text = response.text.strip()
            
            # If response is wrapped in markdown code block, extract it
            if text.startswith("```json"):
                text = text[7:]  # Remove ```json
                if text.endswith("```"):
                    text = text[:-3]  # Remove trailing ```
                text = text.strip()
            elif text.startswith("```"):
                text = text[3:]  # Remove ```
                if text.endswith("```"):
                    text = text[:-3]  # Remove trailing ```
                text = text.strip()
            
            # Parse JSON
            try:
                result = json.loads(text)
                if not isinstance(result, dict):
                    raise Exception(f"Expected JSON object, got {type(result).__name__}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response: {text}")
                raise Exception(f"Gemini returned invalid JSON: {str(e)}")
        
        except Exception as e:
            logger.error(f"Gemini JSON generation failed: {e}")
            raise Exception(f"Gemini LLM JSON error: {str(e)}")

    def is_available(self) -> bool:
        """
        Check if Gemini provider is available.

        Returns:
            True if provider is configured and accessible.
        """
        return self._available
