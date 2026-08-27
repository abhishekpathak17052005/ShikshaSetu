"""OpenAI LLM Provider for real API calls."""
import json
from typing import Optional

from openai import OpenAI, APIError, RateLimitError

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """
    Real OpenAI LLM provider.
    
    Uses the OpenAI API to generate text and JSON responses.
    Requires LLM_API_KEY environment variable.
    """

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key.
            model: Model name (e.g., "gpt-3.5-turbo", "gpt-4").
        """
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text using OpenAI API.

        Args:
            prompt: The input prompt for the LLM.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0-1).

        Returns:
            Generated text response.

        Raises:
            APIError: If API call fails.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except (APIError, RateLimitError) as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def generate_json(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> dict:
        """
        Generate JSON using OpenAI API.

        Args:
            prompt: The input prompt for the LLM.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0-1).

        Returns:
            Parsed JSON response as dictionary.

        Raises:
            APIError: If API call fails.
            json.JSONDecodeError: If response is not valid JSON.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except (APIError, RateLimitError) as e:
            raise Exception(f"OpenAI API error: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in LLM response: {str(e)}")

    def is_available(self) -> bool:
        """
        Check if OpenAI provider is properly configured.

        Returns:
            True if API key is present and valid.
        """
        return bool(self.api_key and self.api_key.strip())
