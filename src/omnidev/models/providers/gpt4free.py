"""
GPT4Free provider implementation.

Integrates with the g4f library to provide free access to AI models
with automatic failover to working providers.
"""

import asyncio
from typing import Any, Optional

try:
    import g4f
    from g4f import Provider
    from g4f.client import Client
    from g4f.errors import RateLimitError, RetryProviderError
except ImportError:
    g4f = None
    Provider = None
    Client = None
    RateLimitError = Exception
    RetryProviderError = Exception

from omnidev.core.exceptions import ProviderError
from omnidev.models.base import BaseProvider, ProviderResponse


class GPT4FreeProvider(BaseProvider):
    """Provider for GPT4Free (free AI model access).

    Automatically handles provider failover and health monitoring.
    """

    # Default models available through g4f
    # Note: Some providers like DDG may have different model names
    # These are commonly supported across multiple providers
    DEFAULT_MODELS = [
        "gpt-4",  # Most widely supported
        "gpt-3.5-turbo",  # Very widely supported
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "gemini-pro",
        "gemini-pro-1.5",
        "deepseek-chat",
        "llama-3.1-70b",  # Meta models
        "mixtral-8x7b",  # Mistral models
    ]
    
    # Models to try as fallback if requested model is not available
    FALLBACK_MODELS = ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet"]

    # Default providers to try in order (known working providers in g4f 6.8.x)
    # Note: Many providers require additional packages or API keys
    DEFAULT_PROVIDERS = [
        "PollinationsAI",  # Usually works without extra setup
        "Chatai",
        "ItalyGPT",
        "FenayAI",
        "EasyChat",
        "WeWordle",
        "DeepInfra",  # May need models to be specified
        "Qwen",  # Qwen models
    ]

    def __init__(
        self, 
        api_key: Optional[str] = None, 
        strict: bool = False,
        preferred_providers: Optional[list[str]] = None,
    ) -> None:
        """Initialize GPT4Free provider.

        Args:
            api_key: Not used for GPT4Free (free provider).
            strict: If True, raise errors on initialization failure. If False, allow partial initialization.
            preferred_providers: Optional list of provider names to try in order.
                               If None, uses DEFAULT_PROVIDERS.
        """
        super().__init__(name="gpt4free", api_key=None)
        self.client: Optional[Client] = None
        self.working_providers: list[str] = []
        self.failed_providers: set[str] = set()
        self._initialized = False
        self.preferred_providers = preferred_providers or self.DEFAULT_PROVIDERS.copy()

        if g4f is None:
            if strict:
                raise ProviderError("g4f library is not installed. Install it with: pip install g4f")
            # Non-strict mode: log warning but allow initialization
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("g4f library is not installed. GPT4Free provider will not be fully functional.")
            return

        try:
            self.client = Client()
            self._discover_working_providers()
            self._initialized = True
        except Exception as e:
            self.handle_error(e)
            if strict:
                raise ProviderError(f"Failed to initialize GPT4Free provider: {e}") from e
            # Non-strict mode: log warning but allow partial initialization
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"GPT4Free provider initialization had issues: {e}. Some features may not work.")
            # Set preferred providers as fallback
            self.working_providers = self.preferred_providers.copy()

    def _discover_working_providers(self) -> None:
        """Discover which providers are currently working.

        This is a best-effort discovery. Actual availability
        is checked during request time. Uses preferred_providers
        from configuration if available.
        """
        if Provider is None:
            return

        # Try to get available providers
        try:
            # Get all provider classes from g4f
            all_available = [p for p in dir(Provider) if not p.startswith("_")]
            
            # Filter preferred providers to only those that exist in g4f
            # This ensures we use the user's preference order but only valid providers
            self.working_providers = [
                p for p in self.preferred_providers 
                if p in all_available
            ]
            
            # If no preferred providers are available, fall back to defaults
            if not self.working_providers:
                self.working_providers = [
                    p for p in self.DEFAULT_PROVIDERS 
                    if p in all_available
                ]
        except Exception:
            # If discovery fails, use preferred providers list
            self.working_providers = self.preferred_providers.copy()

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Generate a response using GPT4Free.

        Args:
            prompt: Input prompt/text.
            model: Optional specific model to use. Defaults to gpt-4o.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0.0 to 2.0).
            **kwargs: Additional parameters (ignored for g4f).

        Returns:
            ProviderResponse with generated content.

        Raises:
            ProviderError: If generation fails after all retries.
        """
        if not self._initialized or not self.client:
            # Try to initialize now if not already done
            if g4f is None:
                raise ProviderError("g4f library is not installed. Install it with: pip install g4f")
            try:
                self.client = Client()
                self._discover_working_providers()
                self._initialized = True
            except Exception as e:
                raise ProviderError(f"GPT4Free client not initialized: {e}") from e

        if not prompt or not prompt.strip():
            raise ProviderError("Prompt cannot be empty")

        model = model or "gpt-4"  # Use gpt-4 as default (more widely supported)

        # Try providers in priority order
        last_error: Optional[Exception] = None
        
        # Models to try (start with requested model, then fallbacks)
        models_to_try = [model] + [m for m in self.FALLBACK_MODELS if m != model]

        for provider_name in self.working_providers:
            if provider_name in self.failed_providers:
                continue

            # Try each model with this provider
            for try_model in models_to_try:
                try:
                    response = await self._try_provider(provider_name, try_model, prompt, max_tokens, temperature, system_prompt)
                    # Success - reset health and return
                    self.reset_health()
                    self.failed_providers.discard(provider_name)
                    return response
                except (RateLimitError, RetryProviderError) as e:
                    # Rate limited or provider error - try next
                    last_error = e
                    continue
                except Exception as e:
                    # Model not found or other error - try next model
                    if "model_not_found" in str(e).lower() or "not exist" in str(e).lower():
                        continue
                    last_error = e
                    continue
            
            # If all models failed for this provider, mark it as failed
            self.failed_providers.add(provider_name)

        # All providers failed
        self.handle_error(last_error or Exception("All providers failed"))
        raise ProviderError(f"All GPT4Free providers failed. Last error: {last_error}")

    async def _try_provider(
        self,
        provider_name: str,
        model: str,
        prompt: str,
        max_tokens: Optional[int],
        temperature: float,
        system_prompt: Optional[str] = None,
    ) -> ProviderResponse:
        """Try to generate using a specific provider.

        Args:
            provider_name: Name of the provider to try.
            model: Model name.
            prompt: Input prompt.
            max_tokens: Maximum tokens.
            temperature: Temperature setting.

        Returns:
            ProviderResponse with generated content.

        Raises:
            Exception: If generation fails.
        """
        if Provider is None:
            raise ProviderError("g4f.Provider is not available")

        # Get provider class
        provider_class = getattr(Provider, provider_name, None)
        if provider_class is None:
            raise ProviderError(f"Provider {provider_name} not found")

        # Create provider instance
        provider = provider_class()

        # Prepare messages with system prompt if provided
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
        # Note: g4f uses synchronous API, so we run it in executor
        # For G4F 6.8.x, ChatCompletion.create is still the primary API
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: g4f.ChatCompletion.create(provider=provider, **params),
        )

        # Extract content
        # G4F 6.8.x may return different response formats
        content = None
        if hasattr(response, "choices") and response.choices:
            # Standard OpenAI-compatible format
            choice = response.choices[0]
            if hasattr(choice, "message") and hasattr(choice.message, "content"):
                content = choice.message.content
            elif hasattr(choice, "text"):
                content = choice.text
            elif isinstance(choice, str):
                content = choice
        elif hasattr(response, "text"):
            # Some providers return text directly
            content = response.text
        elif isinstance(response, str):
            # Direct string response
            content = response
        elif hasattr(response, "content"):
            # Some response objects have content attribute
            content = response.content
        
        if content is None:
            raise ProviderError(f"Unexpected response format from {provider_name}: {type(response)}")

        # Estimate tokens (rough estimate: 1 token ≈ 4 characters)
        tokens_used = len(content) // 4 + len(prompt) // 4

        return ProviderResponse(
            content=content,
            model=model,
            provider=f"gpt4free/{provider_name}",
            tokens_used=tokens_used,
            cost=0.0,  # Free
            metadata={"provider": provider_name},
        )

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
        # Provider is healthy if initialized and we have at least one working provider
        if not self._initialized:
            # Try to initialize now
            try:
                if g4f is None:
                    return False
                if not self.client:
                    self.client = Client()
                if not self.working_providers:
                    self._discover_working_providers()
                self._initialized = True
            except Exception:
                return False
        
        return len(self.working_providers) > len(self.failed_providers)

    def reset_health(self) -> None:
        """Reset provider health and clear failed providers."""
        super().reset_health()
        self.failed_providers.clear()

