"""
OpenAI provider implementation.

Uses OpenAI's official API for code generation.
"""

import os
from typing import Any, Optional

from openai import AsyncOpenAI

from omnidev.core.exceptions import ProviderError
from omnidev.models.base import BaseProvider, ProviderResponse


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI's official API."""

    # Available OpenAI models
    DEFAULT_MODELS = [
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
    ]

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key. If None, reads from environment.

        Raises:
            ProviderError: If API key is not provided.
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("OMNIDEV_OPENAI_API_KEY")
        super().__init__(name="openai", api_key=api_key)
        
        if not self.api_key:
            raise ProviderError("OpenAI API key not provided")
        
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Generate a response using OpenAI API.

        Args:
            prompt: Input prompt/text.
            model: Optional specific model to use. Defaults to gpt-4o.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0.0 to 2.0).
            system_prompt: Optional system prompt for the model.
            **kwargs: Additional parameters.

        Returns:
            ProviderResponse with generated content.

        Raises:
            ProviderError: If generation fails.
        """
        if not prompt or not prompt.strip():
            raise ProviderError("Prompt cannot be empty")

        model = model or "gpt-4o"
        if not self.is_model_available(model):
            raise ProviderError(f"Model {model} is not available")

        try:
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Prepare parameters
            params: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens:
                params["max_tokens"] = max_tokens

            # Generate response
            response = await self.client.chat.completions.create(**params)

            # Extract content
            if not response.choices or not response.choices[0].message.content:
                raise ProviderError("Empty response from OpenAI")

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            # Estimate cost (rough estimates)
            cost = self._estimate_cost(model, tokens_used)

            return ProviderResponse(
                content=content,
                model=model,
                provider="openai",
                tokens_used=tokens_used,
                cost=cost,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "response_id": response.id,
                },
            )
        except Exception as e:
            self.handle_error(e)
            raise ProviderError(f"OpenAI generation failed: {e}") from e

    def list_models(self) -> list[str]:
        """List available models.

        Returns:
            List of available model names.
        """
        return self.DEFAULT_MODELS.copy()

    def is_model_available(self, model: str) -> bool:
        """Check if a model is available.

        Args:
            model: Model name to check.

        Returns:
            True if model is in the available list, False otherwise.
        """
        return model in self.DEFAULT_MODELS

    def check_health(self) -> bool:
        """Check provider health.

        Returns:
            True if provider is healthy, False otherwise.
        """
        return self.is_available and self.api_key is not None

    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate cost for API usage.

        Args:
            model: Model name.
            tokens: Number of tokens used.

        Returns:
            Estimated cost in USD.
        """
        # Rough cost estimates per 1M tokens (as of 2024)
        costs = {
            "gpt-4o": 2.50,  # $2.50 per 1M input tokens, $10 per 1M output tokens (average)
            "gpt-4-turbo": 10.00,  # $10 per 1M input tokens, $30 per 1M output tokens (average)
            "gpt-4o-mini": 0.15,  # $0.15 per 1M input tokens, $0.60 per 1M output tokens (average)
            "gpt-3.5-turbo": 0.50,  # $0.50 per 1M input tokens, $1.50 per 1M output tokens (average)
        }
        
        base_cost = costs.get(model, 2.50)
        return (tokens / 1_000_000) * base_cost

