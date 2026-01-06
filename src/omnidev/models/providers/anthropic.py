"""
Anthropic/Claude provider implementation.

Uses Anthropic's official API for code generation.
"""

import os
from typing import Any, Optional

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    AsyncAnthropic = None
    ANTHROPIC_AVAILABLE = False

from omnidev.core.exceptions import ProviderError
from omnidev.models.base import BaseProvider, ProviderResponse


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic's official Claude API."""

    # Available Anthropic models
    DEFAULT_MODELS = [
        "claude-sonnet-4-20250514",
        "claude-opus-4-20250514",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]
    
    # Model aliases for convenience
    MODEL_ALIASES = {
        "claude-sonnet-4": "claude-sonnet-4-20250514",
        "claude-opus-4": "claude-opus-4-20250514",
        "claude-3.5-sonnet": "claude-3-5-sonnet-20241022",
        "claude-3.5-haiku": "claude-3-5-haiku-20241022",
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-sonnet": "claude-3-sonnet-20240229",
        "claude-3-haiku": "claude-3-haiku-20240307",
    }

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key. If None, reads from environment.

        Raises:
            ProviderError: If API key is not provided or library not available.
        """
        if not ANTHROPIC_AVAILABLE:
            raise ProviderError(
                "Anthropic library is not installed. Install it with: pip install anthropic"
            )
        
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OMNIDEV_ANTHROPIC_API_KEY")
        super().__init__(name="anthropic", api_key=api_key)
        
        if not self.api_key:
            raise ProviderError("Anthropic API key not provided")
        
        self.client = AsyncAnthropic(api_key=self.api_key)

    def _resolve_model(self, model: str) -> str:
        """Resolve model alias to full model name.
        
        Args:
            model: Model name or alias.
            
        Returns:
            Full model name.
        """
        return self.MODEL_ALIASES.get(model, model)

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Generate a response using Anthropic API.

        Args:
            prompt: Input prompt/text.
            model: Optional specific model to use. Defaults to claude-sonnet-4.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0.0 to 1.0).
            system_prompt: Optional system prompt for the model.
            **kwargs: Additional parameters.

        Returns:
            ProviderResponse with generated content.

        Raises:
            ProviderError: If generation fails.
        """
        if not prompt or not prompt.strip():
            raise ProviderError("Prompt cannot be empty")

        model = self._resolve_model(model or "claude-sonnet-4")
        max_tokens = max_tokens or 4096

        try:
            # Prepare parameters
            params: dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }
            
            if system_prompt:
                params["system"] = system_prompt

            # Generate response
            response = await self.client.messages.create(**params)

            # Extract content
            if not response.content:
                raise ProviderError("Empty response from Anthropic")

            content = response.content[0].text
            
            # Calculate tokens used
            input_tokens = response.usage.input_tokens if response.usage else 0
            output_tokens = response.usage.output_tokens if response.usage else 0
            tokens_used = input_tokens + output_tokens

            # Estimate cost
            cost = self._estimate_cost(model, input_tokens, output_tokens)

            return ProviderResponse(
                content=content,
                model=model,
                provider="anthropic",
                tokens_used=tokens_used,
                cost=cost,
                metadata={
                    "stop_reason": response.stop_reason,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
            )
        except Exception as e:
            self.handle_error(e)
            raise ProviderError(f"Anthropic generation failed: {e}") from e

    def list_models(self) -> list[str]:
        """List available models.

        Returns:
            List of available model names (aliases for convenience).
        """
        return list(self.MODEL_ALIASES.keys())

    def is_model_available(self, model: str) -> bool:
        """Check if a model is available.

        Args:
            model: Model name to check.

        Returns:
            True if model is available, False otherwise.
        """
        resolved = self._resolve_model(model)
        return resolved in self.DEFAULT_MODELS or model in self.MODEL_ALIASES

    def check_health(self) -> bool:
        """Check provider health.

        Returns:
            True if provider is healthy, False otherwise.
        """
        return self.is_available and self.api_key is not None

    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for API usage.

        Args:
            model: Model name.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Estimated cost in USD.
        """
        # Cost estimates per 1M tokens (as of 2025)
        costs = {
            "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
            "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
            "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
            "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.0},
            "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
            "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
            "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        }
        
        model_costs = costs.get(model, {"input": 3.0, "output": 15.0})
        input_cost = (input_tokens / 1_000_000) * model_costs["input"]
        output_cost = (output_tokens / 1_000_000) * model_costs["output"]
        
        return input_cost + output_cost

