"""Mock LLM Provider for testing without real API calls."""
import json
from typing import Optional

from .base import LLMProvider


class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider for testing.
    
    Returns deterministic, structured responses without calling any real API.
    Useful for testing the entire pipeline without API keys or rate limits.
    """

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate mock text response.

        Args:
            prompt: The input prompt (unused in mock).
            max_tokens: Maximum tokens (unused in mock).
            temperature: Sampling temperature (unused in mock).

        Returns:
            A deterministic mock response.
        """
        # Return a simple mock response
        return "This is a mock LLM response for testing purposes."

    def generate_json(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> dict:
        """
        Generate mock JSON response.

        Args:
            prompt: The input prompt containing the request.
            max_tokens: Maximum tokens (unused in mock).
            temperature: Sampling temperature (unused in mock).

        Returns:
            A deterministic mock JSON response.
        """
        # Return a mock MCQ response based on the prompt
        return {
            "question": "What is the primary purpose of the SQL SELECT statement?",
            "options": [
                "To insert data into tables",
                "To retrieve data from tables",
                "To delete data from tables",
                "To modify table structure"
            ],
            "correct_answer": "B",
            "explanation": "The SQL SELECT statement is used to retrieve and query data from one or more database tables.",
            "difficulty": "MEDIUM",
            "source_chunks": ["chunk_1", "chunk_2"]
        }

    def is_available(self) -> bool:
        """
        Mock provider is always available.

        Returns:
            True, as mock provider doesn't require API keys or external services.
        """
        return True
