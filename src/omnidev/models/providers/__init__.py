"""AI provider implementations for OmniDev."""

from omnidev.models.providers.gpt4free import GPT4FreeProvider
from omnidev.models.providers.openai import OpenAIProvider
from omnidev.models.providers.openrouter import OpenRouterProvider

# Optional providers - import with try/except for optional dependencies
try:
    from omnidev.models.providers.anthropic import AnthropicProvider
except ImportError:
    AnthropicProvider = None  # type: ignore

try:
    from omnidev.models.providers.google import GoogleProvider
except ImportError:
    GoogleProvider = None  # type: ignore

try:
    from omnidev.models.providers.groq import GroqProvider
except ImportError:
    GroqProvider = None  # type: ignore

__all__ = [
    "GPT4FreeProvider", 
    "OpenAIProvider", 
    "OpenRouterProvider",
    "AnthropicProvider",
    "GoogleProvider",
    "GroqProvider",
]
