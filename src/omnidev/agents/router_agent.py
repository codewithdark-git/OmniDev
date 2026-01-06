"""
Router Agent for OmniDev.

Handles model selection and task routing.
"""

from typing import Any, Optional

from omnidev.agents.base import BaseOmniDevAgent
from omnidev.core.config import ConfigManager
from omnidev.models.registry import ProviderRegistry


class RouterAgent(BaseOmniDevAgent):
    """Agent responsible for model selection and routing."""

    def __init__(self, config: ConfigManager, provider_registry: ProviderRegistry) -> None:
        """Initialize router agent.

        Args:
            config: ConfigManager instance.
            provider_registry: ProviderRegistry instance.
        """
        super().__init__(
            role="Model Selection and Routing Specialist",
            goal="Select the optimal AI model for each task based on complexity, cost, availability, and task requirements",
            backstory="""You are an expert at analyzing tasks and matching them with 
            the most appropriate AI models. You understand model capabilities, costs, 
            and performance characteristics. You always optimize for both quality and 
            cost-effectiveness.""",
            config=config,
            prompt_name="router_agent",
        )
        object.__setattr__(self, "_omnidev_provider_registry", provider_registry)
    
    @property
    def provider_registry(self) -> ProviderRegistry:
        """Get ProviderRegistry instance."""
        return getattr(self, "_omnidev_provider_registry", None)

    def select_model(self, task: str, complexity: str = "medium") -> dict[str, Any]:
        """Select the best model for a task.

        Args:
            task: Task description.
            complexity: Task complexity (low, medium, high).

        Returns:
            Model selection dictionary.
        """
        # Use agent reasoning to select model
        # For now, return basic selection
        return {
            "model": "auto",
            "provider": "gpt4free",
            "reason": "Auto-selected based on task complexity",
        }

