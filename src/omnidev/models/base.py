"""
Base provider interface for AI models.

Defines the abstract base class that all AI providers must implement,
providing a standardized interface for model interactions.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from omnidev.core.exceptions import ProviderError


class ProviderResponse:
    """Response from an AI provider."""

    def __init__(
        self,
        content: str,
        model: str,
        provider: str,
        tokens_used: int = 0,
        cost: float = 0.0,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize provider response.

        Args:
            content: Generated content/text.
            model: Model name used.
            provider: Provider name.
            tokens_used: Number of tokens used.
            cost: Cost in USD.
            metadata: Optional additional metadata.
        """
        self.content = content
        self.model = model
        self.provider = provider
        self.tokens_used = tokens_used
        self.cost = cost
        self.metadata = metadata or {}


class BaseProvider(ABC):
    """Abstract base class for all AI providers.

    All providers must implement this interface to ensure consistent
    behavior across different AI services.
    """

    def __init__(self, name: str, api_key: Optional[str] = None) -> None:
        """Initialize the provider.

        Args:
            name: Provider name.
            api_key: Optional API key for the provider.
        """
        self.name = name
        self.api_key = api_key
        self.is_available = True
        self.last_error: Optional[str] = None

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Generate a response from the AI model.

        Args:
            prompt: Input prompt/text.
            model: Optional specific model to use.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0.0 to 2.0).
            system_prompt: Optional system prompt for the model.
            **kwargs: Additional provider-specific parameters.

        Returns:
            ProviderResponse with generated content and metadata.

        Raises:
            ProviderError: If generation fails.
        """
        pass

    @abstractmethod
    def list_models(self) -> list[str]:
        """List available models for this provider.

        Returns:
            List of available model names.
        """
        pass

    @abstractmethod
    def is_model_available(self, model: str) -> bool:
        """Check if a specific model is available.

        Args:
            model: Model name to check.

        Returns:
            True if model is available, False otherwise.
        """
        pass

    def check_health(self) -> bool:
        """Check if the provider is healthy and available.

        Returns:
            True if provider is available, False otherwise.
        """
        return self.is_available

    def get_cost_estimate(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Estimate the cost for a request.

        Args:
            prompt_tokens: Number of input tokens.
            completion_tokens: Number of output tokens.
            model: Model name.

        Returns:
            Estimated cost in USD.
        """
        # Default implementation returns 0.0 (free)
        # Subclasses should override with actual pricing
        return 0.0

    def handle_error(self, error: Exception) -> None:
        """Handle an error from the provider.

        Args:
            error: Exception that occurred.
        """
        self.is_available = False
        self.last_error = str(error)

    def reset_health(self) -> None:
        """Reset provider health status."""
        self.is_available = True
        self.last_error = None

    def __repr__(self) -> str:
        """String representation of the provider."""
        status = "available" if self.is_available else "unavailable"
        return f"{self.__class__.__name__}(name={self.name!r}, status={status})"

