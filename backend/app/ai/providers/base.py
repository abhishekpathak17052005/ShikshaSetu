"""Abstract LLM Provider base class."""
from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM implementations must inherit from this class and implement
    the required abstract methods.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text using the LLM.

        Args:
            prompt: The input prompt for the LLM.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0-1).

        Returns:
            Generated text response.

        Raises:
            Exception: If generation fails.
        """
        pass

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> dict:
        """
        Generate a JSON response using the LLM.

        Args:
            prompt: The input prompt for the LLM.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0-1).

        Returns:
            Parsed JSON response as dictionary.

        Raises:
            Exception: If generation or JSON parsing fails.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is properly configured and available.

        Returns:
            True if the provider can be used, False otherwise.
        """
        pass
