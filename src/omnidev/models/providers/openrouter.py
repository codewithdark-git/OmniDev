"""
OpenRouter provider for agent internal operations.

This provider is used exclusively for agent orchestration tasks,
NOT for code generation or user-facing text generation.
"""

import os
from typing import Any, AsyncIterator, Optional

import httpx

from omnidev.core.exceptions import ProviderError
from omnidev.models.base import BaseProvider, ProviderResponse


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider for agent operations."""

    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, api_key: Optional[str] = None, model: str = "openai/gpt-4o-mini") -> None:
        """Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key. If None, reads from environment.
            model: Model identifier (default: gpt-4o-mini for cost efficiency).
        """
        super().__init__(name="openrouter", api_key=api_key or os.getenv("OPENROUTER_API_KEY"))
        if not self.api_key:
            raise ProviderError("OpenRouter API key not provided")
        
        self.model = model
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/omnidev/omnidev",
                "X-Title": "OmniDev",
            },
            timeout=60.0,
        )

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Generate response using OpenRouter.

        Args:
            prompt: User prompt.
            model: Model to use (defaults to instance model).
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            system_prompt: Optional system prompt.
            **kwargs: Additional parameters.

        Returns:
            ProviderResponse with generated text.

        Raises:
            ProviderError: If generation fails.
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            model_to_use = model or self.model
            payload = {
                "model": model_to_use,
                "messages": messages,
                "temperature": temperature,
                **kwargs,
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens

            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            choice = data["choices"][0]
            content = choice["message"]["content"]
            
            usage_data = data.get("usage", {})
            return ProviderResponse(
                content=content,
                model=model_to_use,
                provider=self.name,
                tokens_used=usage_data.get("total_tokens", 0),
                cost=0.0,  # OpenRouter cost calculation would go here
                metadata={
                    "id": data.get("id"),
                    "created": data.get("created"),
                    "finish_reason": choice.get("finish_reason"),
                    "usage": usage_data,
                },
            )
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"OpenRouter API error: {e.response.text}") from e
        except Exception as e:
            raise ProviderError(f"OpenRouter generation failed: {e}") from e

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream response from OpenRouter.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional parameters.

        Yields:
            Text chunks as they arrive.

        Raises:
            ProviderError: If streaming fails.
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
                **kwargs,
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens

            async with self.client.stream("POST", "/chat/completions", json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line.strip() or line.startswith("data: [DONE]"):
                        continue
                    
                    if line.startswith("data: "):
                        import json
                        data = json.loads(line[6:])
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"OpenRouter streaming error: {e.response.text}") from e
        except Exception as e:
            raise ProviderError(f"OpenRouter streaming failed: {e}") from e

    # Common OpenRouter models for synchronous listing
    COMMON_MODELS = [
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "openai/gpt-4-turbo",
        "anthropic/claude-sonnet-4-20250514",
        "anthropic/claude-3-5-sonnet",
        "anthropic/claude-3-opus",
        "google/gemini-2.0-flash",
        "google/gemini-1.5-pro",
        "mistralai/mistral-large",
        "deepseek/deepseek-r1",
        "deepseek/deepseek-chat",
        "meta-llama/llama-3.1-405b-instruct",
    ]

    def list_models(self) -> list[str]:
        """List common available models from OpenRouter.

        Returns:
            List of common model identifiers.
        """
        # Return common models for synchronous use
        # For full list, use list_models_async
        return self.COMMON_MODELS.copy()

    async def list_models_async(self) -> list[str]:
        """List all available models from OpenRouter asynchronously.

        Returns:
            List of model identifiers.

        Raises:
            ProviderError: If listing fails.
        """
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            data = response.json()
            models = data.get("data", [])
            return [model.get("id", "") for model in models if model.get("id")]
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"OpenRouter API error: {e.response.text}") from e
        except Exception as e:
            raise ProviderError(f"Failed to list OpenRouter models: {e}") from e

    def is_model_available(self, model: str) -> bool:
        """Check if a model is available (synchronous check).

        Args:
            model: Model identifier to check.

        Returns:
            True if model is likely available (basic check).
        """
        # For OpenRouter, we assume models are available if they match the pattern
        # Full check would require async call, so this is a best-effort check
        return bool(model and "/" in model)

    async def list_models_detailed(self) -> list[dict[str, Any]]:
        """List available models with detailed information.

        Returns:
            List of model dictionaries with full details.

        Raises:
            ProviderError: If listing fails.
        """
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"OpenRouter API error: {e.response.text}") from e
        except Exception as e:
            raise ProviderError(f"Failed to list OpenRouter models: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    def __del__(self) -> None:
        """Cleanup on deletion."""
        # Note: This won't work for async cleanup, but helps with warnings
        if hasattr(self, "client"):
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.client.aclose())
            except Exception:
                pass

