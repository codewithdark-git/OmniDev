"""
Provider registry for managing AI providers.

Handles provider registration, discovery, health checking, and fallback chains.
"""

from typing import Optional

from omnidev.core.config import ConfigManager
from omnidev.core.exceptions import ProviderError
from omnidev.core.logger import get_logger
from omnidev.models.base import BaseProvider
from omnidev.models.providers.gpt4free import GPT4FreeProvider
from omnidev.models.providers.openai import OpenAIProvider


class ProviderRegistry:
    """Registry for managing AI providers.

    Handles registration, discovery, health checking, and provides
    fallback chains for reliable provider access.
    """

    def __init__(self, config: Optional[ConfigManager] = None, auto_register: bool = False) -> None:
        """Initialize the provider registry.

        Args:
            config: Optional configuration manager.
            auto_register: If True, automatically register default providers (default: False).
        """
        self.config = config
        self.logger = get_logger("registry")
        self.providers: dict[str, BaseProvider] = {}
        self.provider_priority: list[str] = []
        self._priority_values: dict[str, int] = {}  # Track actual priority numbers
        
        if auto_register:
            self._initialize_default_providers()

    def _initialize_default_providers(self) -> None:
        """Initialize default providers (lazy registration).
        
        The configured provider (from config.models.fallback) gets priority 0 (highest).
        Other providers get higher priority numbers (lower priority).
        """
        # Get configured provider from config
        configured_provider = None
        g4f_providers = None
        if self.config:
            config = self.config.get_config()
            configured_provider = config.models.fallback
            g4f_providers = config.models.g4f_providers
        
        # Determine GPT4Free priority based on whether it's the configured provider
        gpt4free_priority = 0 if configured_provider == "gpt4free" else 10
        
        # Try to register GPT4Free with appropriate priority
        self.register_provider_lazy(
            "gpt4free", 
            lambda: GPT4FreeProvider(preferred_providers=g4f_providers), 
            priority=gpt4free_priority
        )

        # Register official API providers if API keys are available
        if self.config:
            self._register_official_providers(configured_provider)

    def _register_official_providers(self, configured_provider: Optional[str] = None) -> None:
        """Register official API providers if API keys are available.
        
        Args:
            configured_provider: The provider configured as primary in settings.
                               This provider gets priority 0, others get higher priority.
        """
        if not self.config:
            return
        
        # Register OpenAI if API key is available
        openai_key = self.config.get_api_key("openai")
        if openai_key:
            try:
                # Configured provider gets priority 0, others get higher priority
                priority = 0 if configured_provider == "openai" else 5
                self.register_provider_lazy(
                    "openai",
                    lambda: OpenAIProvider(api_key=openai_key),
                    priority=priority,
                )
            except Exception as e:
                self.logger.warning(f"Failed to register OpenAI provider: {e}")
        
        # Register Anthropic if API key is available
        anthropic_key = self.config.get_api_key("anthropic")
        if anthropic_key:
            try:
                from omnidev.models.providers.anthropic import AnthropicProvider
                priority = 0 if configured_provider == "anthropic" else 5
                self.register_provider_lazy(
                    "anthropic",
                    lambda: AnthropicProvider(api_key=anthropic_key),
                    priority=priority,
                )
            except Exception as e:
                self.logger.warning(f"Failed to register Anthropic provider: {e}")
        
        # Register Google if API key is available
        google_key = self.config.get_api_key("google")
        if google_key:
            try:
                from omnidev.models.providers.google import GoogleProvider
                priority = 0 if configured_provider == "google" else 5
                self.register_provider_lazy(
                    "google",
                    lambda: GoogleProvider(api_key=google_key),
                    priority=priority,
                )
            except Exception as e:
                self.logger.warning(f"Failed to register Google provider: {e}")
        
        # Register OpenRouter if API key is available
        openrouter_key = self.config.get_api_key("openrouter")
        if openrouter_key:
            try:
                from omnidev.models.providers.openrouter import OpenRouterProvider
                priority = 0 if configured_provider == "openrouter" else 5
                self.register_provider_lazy(
                    "openrouter",
                    lambda: OpenRouterProvider(api_key=openrouter_key),
                    priority=priority,
                )
            except Exception as e:
                self.logger.warning(f"Failed to register OpenRouter provider: {e}")
        
        # Register Groq if API key is available
        groq_key = self.config.get_api_key("groq")
        if groq_key:
            try:
                from omnidev.models.providers.groq import GroqProvider
                priority = 0 if configured_provider == "groq" else 5
                self.register_provider_lazy(
                    "groq",
                    lambda: GroqProvider(api_key=groq_key),
                    priority=priority,
                )
            except Exception as e:
                self.logger.warning(f"Failed to register Groq provider: {e}")
    
    def register_provider_lazy(
        self, 
        name: str, 
        provider_factory: callable, 
        priority: int = 10,
        check_health: bool = False
    ) -> bool:
        """Register a provider lazily (only when needed).
        
        Args:
            name: Provider name/identifier.
            provider_factory: Callable that returns a BaseProvider instance.
            priority: Priority for fallback chain (lower = higher priority).
            check_health: If True, check provider health before registering.
            
        Returns:
            True if provider was registered successfully, False otherwise.
        """
        try:
            provider = provider_factory()
            if not isinstance(provider, BaseProvider):
                self.logger.warning(f"Provider factory for {name} did not return BaseProvider")
                return False
            
            # Optional health check
            if check_health:
                if not provider.check_health():
                    self.logger.warning(f"Provider {name} failed health check, not registering")
                    return False
            
            self.register_provider(name, provider, priority)
            return True
        except Exception as e:
            self.logger.warning(f"Failed to register provider {name} lazily: {e}")
            return False
    
    def ensure_provider_registered(self, name: str, priority: int = 5) -> bool:
        """Ensure a provider is registered, registering it if needed.
        
        Args:
            name: Provider name to ensure is registered.
            priority: Priority for the provider (lower = higher priority).
            
        Returns:
            True if provider is available, False otherwise.
        """
        if name in self.providers:
            return True
        
        # Get g4f_providers from config if available
        g4f_providers = None
        if self.config:
            config = self.config.get_config()
            g4f_providers = config.models.g4f_providers
        
        # Try to register common providers
        if name == "gpt4free":
            return self.register_provider_lazy(
                "gpt4free", 
                lambda: GPT4FreeProvider(preferred_providers=g4f_providers), 
                priority=priority
            )
        elif name == "openai":
            if not self.config:
                return False
            api_key = self.config.get_api_key("openai")
            if api_key:
                return self.register_provider_lazy(
                    "openai",
                    lambda: OpenAIProvider(api_key=api_key),
                    priority=priority,
                )
        elif name == "anthropic":
            if not self.config:
                return False
            api_key = self.config.get_api_key("anthropic")
            if api_key:
                try:
                    from omnidev.models.providers.anthropic import AnthropicProvider
                    return self.register_provider_lazy(
                        "anthropic",
                        lambda: AnthropicProvider(api_key=api_key),
                        priority=priority,
                    )
                except ImportError:
                    self.logger.warning("Anthropic provider not available")
        elif name == "google":
            if not self.config:
                return False
            api_key = self.config.get_api_key("google")
            if api_key:
                try:
                    from omnidev.models.providers.google import GoogleProvider
                    return self.register_provider_lazy(
                        "google",
                        lambda: GoogleProvider(api_key=api_key),
                        priority=priority,
                    )
                except ImportError:
                    self.logger.warning("Google provider not available")
        elif name == "openrouter":
            if not self.config:
                return False
            api_key = self.config.get_api_key("openrouter")
            if api_key:
                try:
                    from omnidev.models.providers.openrouter import OpenRouterProvider
                    return self.register_provider_lazy(
                        "openrouter",
                        lambda: OpenRouterProvider(api_key=api_key),
                        priority=priority,
                    )
                except ImportError:
                    self.logger.warning("OpenRouter provider not available")
        elif name == "groq":
            if not self.config:
                return False
            api_key = self.config.get_api_key("groq")
            if api_key:
                try:
                    from omnidev.models.providers.groq import GroqProvider
                    return self.register_provider_lazy(
                        "groq",
                        lambda: GroqProvider(api_key=api_key),
                        priority=priority,
                    )
                except ImportError:
                    self.logger.warning("Groq provider not available")
        
        return False

    def register_provider(self, name: str, provider: BaseProvider, priority: int = 10) -> None:
        """Register a provider.

        Args:
            name: Provider name/identifier.
            provider: Provider instance.
            priority: Priority for fallback chain (lower = higher priority).
        """
        if not isinstance(provider, BaseProvider):
            raise ProviderError(f"Provider must be an instance of BaseProvider, got {type(provider)}")

        self.providers[name] = provider
        self._priority_values[name] = priority

        # Rebuild priority list based on actual priority values
        self._rebuild_priority_list()

        self.logger.info(f"Registered provider: {name} (priority: {priority})")
    
    def _rebuild_priority_list(self) -> None:
        """Rebuild the priority list based on priority values."""
        # Sort providers by their priority value (lower = first)
        self.provider_priority = sorted(
            self._priority_values.keys(),
            key=lambda name: self._priority_values.get(name, 999)
        )

    def unregister_provider(self, name: str) -> None:
        """Unregister a provider.

        Args:
            name: Provider name to unregister.
        """
        if name in self.providers:
            del self.providers[name]
            if name in self._priority_values:
                del self._priority_values[name]
            if name in self.provider_priority:
                self.provider_priority.remove(name)
            self.logger.info(f"Unregistered provider: {name}")

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get a provider by name.

        Args:
            name: Provider name.

        Returns:
            Provider instance if found, None otherwise.
        """
        return self.providers.get(name)

    def list_providers(self) -> list[str]:
        """List all registered provider names.

        Returns:
            List of provider names.
        """
        return list(self.providers.keys())

    def get_fallback_chain(self, preferred_provider: Optional[str] = None) -> list[BaseProvider]:
        """Get fallback chain of providers.

        Args:
            preferred_provider: Optional preferred provider name.

        Returns:
            List of providers in fallback order.
        """
        chain = []

        # Add preferred provider first if specified and available
        if preferred_provider and preferred_provider in self.providers:
            provider = self.providers[preferred_provider]
            if provider.check_health():
                chain.append(provider)

        # Add remaining providers in priority order
        for name in self.provider_priority:
            if name == preferred_provider:
                continue
            provider = self.providers[name]
            if provider.check_health():
                chain.append(provider)

        return chain

    def check_all_health(self) -> dict[str, bool]:
        """Check health of all providers.

        Returns:
            Dictionary mapping provider names to health status.
        """
        health_status = {}
        for name, provider in self.providers.items():
            try:
                health_status[name] = provider.check_health()
            except Exception as e:
                self.logger.warning(f"Error checking health of {name}: {e}")
                health_status[name] = False
        return health_status

    def get_available_providers(self) -> list[str]:
        """Get list of available (healthy) providers.

        Returns:
            List of provider names that are currently available.
        """
        return [name for name, provider in self.providers.items() if provider.check_health()]

    def _get_provider_priority(self, name: str) -> int:
        """Get priority of a provider (for internal use).

        Args:
            name: Provider name.

        Returns:
            Priority value (lower = higher priority).
        """
        return self._priority_values.get(name, 999)

    def reset_all_health(self) -> None:
        """Reset health status for all providers."""
        for provider in self.providers.values():
            provider.reset_health()
        self.logger.info("Reset health status for all providers")

