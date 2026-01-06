"""
Groq provider implementation.

Uses Groq's fast inference API. Free tier available with rate limits.
Get your API key at: https://console.groq.com
"""

import os
from typing import Any, Optional

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    AsyncGroq = None
    GROQ_AVAILABLE = False

from omnidev.core.exceptions import ProviderError
from omnidev.models.base import BaseProvider, ProviderResponse


class GroqProvider(BaseProvider):
    """Provider for Groq's fast inference API.
    
    Groq offers free API access with rate limits:
    - Free tier: 30 requests/minute for most models
    - Very fast inference (claimed fastest)
    """

    # Available Groq models
    DEFAULT_MODELS = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-safeguard-20b",
        "moonshotai/kimi-k2-instruct-0905",
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "meta-llama/llama-guard-4-12b",
    ]
    
    # Model aliases for convenience
    MODEL_ALIASES = {
        "gpt-oss-120b": "openai/gpt-oss-120b",
        "gpt-oss-20bb": "openai/gpt-oss-20b",
        "gpt-oss-safeguard-20b": "openai/gpt-oss-safeguard-20b",
        "kimi-k2": "moonshotai/kimi-k2-instruct-0905",
        "llama-3.1-8b": "llama-3.1-8b-instant",
        "llama-3.3-70b": "llama-3.3-70b-versatile",
        "llama-4-maverick": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "llama-4-guard": "meta-llama/llama-guard-4-12b",
    }

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize Groq provider.

        Args:
            api_key: Groq API key. If None, reads from environment.

        Raises:
            ProviderError: If API key is not provided or library not available.
        """
        if not GROQ_AVAILABLE:
            raise ProviderError(
                "Groq library is not installed. Install it with: pip install groq"
            )
        
        api_key = api_key or os.getenv("GROQ_API_KEY") or os.getenv("OMNIDEV_GROQ_API_KEY")
        super().__init__(name="groq", api_key=api_key)
        
        if not self.api_key:
            raise ProviderError("Groq API key not provided")
        
        self.client = AsyncGroq(api_key=self.api_key)

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
        """Generate a response using Groq API.

        Args:
            prompt: Input prompt/text.
            model: Optional specific model to use. Defaults to llama-3.3-70b-versatile.
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

        model = self._resolve_model(model or "llama-3.3-70b-versatile")
        
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
                raise ProviderError("Empty response from Groq")

            content = response.choices[0].message.content
            
            # Calculate tokens used
            usage = response.usage
            tokens_used = usage.total_tokens if usage else 0

            return ProviderResponse(
                content=content,
                model=model,
                provider="groq",
                tokens_used=tokens_used,
                cost=0.0,  # Groq free tier
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "response_id": response.id,
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                },
            )
        except Exception as e:
            self.handle_error(e)
            raise ProviderError(f"Groq generation failed: {e}") from e

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

