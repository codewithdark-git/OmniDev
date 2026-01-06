"""
Google/Gemini provider implementation.

Uses Google's Generative AI API for code generation.
"""

import os
from typing import Any, Optional

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    genai = None
    GOOGLE_AVAILABLE = False

from omnidev.core.exceptions import ProviderError
from omnidev.models.base import BaseProvider, ProviderResponse


class GoogleProvider(BaseProvider):
    """Provider for Google's Gemini API."""

    # Available Google models
    DEFAULT_MODELS = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-pro",
    ]
    
    # Model aliases for convenience
    MODEL_ALIASES = {
        "gemini-2-flash": "gemini-2.0-flash",
        "gemini-2-flash-lite": "gemini-2.0-flash-lite",
        "gemini-1.5-pro-latest": "gemini-1.5-pro",
        "gemini-1.5-flash-latest": "gemini-1.5-flash",
        "gemini-pro-latest": "gemini-pro",
    }

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize Google provider.

        Args:
            api_key: Google API key. If None, reads from environment.

        Raises:
            ProviderError: If API key is not provided or library not available.
        """
        if not GOOGLE_AVAILABLE:
            raise ProviderError(
                "Google Generative AI library is not installed. "
                "Install it with: pip install google-generativeai"
            )
        
        api_key = (
            api_key 
            or os.getenv("GOOGLE_API_KEY") 
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("OMNIDEV_GOOGLE_API_KEY")
        )
        super().__init__(name="google", api_key=api_key)
        
        if not self.api_key:
            raise ProviderError("Google API key not provided")
        
        # Configure the SDK
        genai.configure(api_key=self.api_key)
        self._model_cache: dict[str, Any] = {}

    def _resolve_model(self, model: str) -> str:
        """Resolve model alias to full model name.
        
        Args:
            model: Model name or alias.
            
        Returns:
            Full model name.
        """
        return self.MODEL_ALIASES.get(model, model)

    def _get_model(self, model_name: str) -> Any:
        """Get or create a GenerativeModel instance.
        
        Args:
            model_name: Model name.
            
        Returns:
            GenerativeModel instance.
        """
        if model_name not in self._model_cache:
            self._model_cache[model_name] = genai.GenerativeModel(model_name)
        return self._model_cache[model_name]

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Generate a response using Google Gemini API.

        Args:
            prompt: Input prompt/text.
            model: Optional specific model to use. Defaults to gemini-2.0-flash.
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

        model_name = self._resolve_model(model or "gemini-2.0-flash")
        
        if not self.is_model_available(model_name):
            raise ProviderError(f"Model {model_name} is not available")

        try:
            # Get model instance
            gemini_model = self._get_model(model_name)
            
            # Prepare generation config
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or 4096,
            )
            
            # Prepare the full prompt with system prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Generate response (Gemini API is synchronous, run in executor)
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: gemini_model.generate_content(
                    full_prompt,
                    generation_config=generation_config,
                ),
            )

            # Extract content
            if not response.text:
                raise ProviderError("Empty response from Google Gemini")

            content = response.text
            
            # Estimate tokens (Gemini doesn't always provide token counts)
            tokens_used = len(content) // 4 + len(prompt) // 4

            # Estimate cost
            cost = self._estimate_cost(model_name, tokens_used)

            return ProviderResponse(
                content=content,
                model=model_name,
                provider="google",
                tokens_used=tokens_used,
                cost=cost,
                metadata={
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None,
                },
            )
        except Exception as e:
            self.handle_error(e)
            raise ProviderError(f"Google Gemini generation failed: {e}") from e

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

    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate cost for API usage.

        Args:
            model: Model name.
            tokens: Estimated number of tokens used.

        Returns:
            Estimated cost in USD.
        """
        # Cost estimates per 1M tokens (as of 2025)
        # Gemini has free tier up to certain limits, paid after that
        costs = {
            "gemini-2.0-flash": 0.10,  # Very affordable
            "gemini-2.0-flash-lite": 0.075,
            "gemini-1.5-pro": 1.25,
            "gemini-1.5-flash": 0.075,
            "gemini-1.5-flash-8b": 0.0375,
            "gemini-pro": 0.50,
        }
        
        base_cost = costs.get(model, 0.10)
        return (tokens / 1_000_000) * base_cost

