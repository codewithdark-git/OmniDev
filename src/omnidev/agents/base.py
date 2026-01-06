"""
Base agent class for OmniDev agents.

Extends CrewAI Agent with OmniDev-specific functionality.
"""

from typing import Any, Optional

from crewai import Agent, LLM

from omnidev.core.config import ConfigManager
from omnidev.models.providers.openrouter import OpenRouterProvider
from omnidev.prompts.loader import PromptLoader


class BaseOmniDevAgent(Agent):
    """Base agent class for all OmniDev agents.

    Extends CrewAI Agent with OpenRouter integration and OmniDev-specific utilities.
    """

    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        config: ConfigManager,
        model: Optional[str] = None,
        prompt_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize base OmniDev agent.

        Args:
            role: Agent role description.
            goal: Agent goal.
            backstory: Agent backstory.
            config: ConfigManager instance.
            model: Optional model override (defaults to config agent_model).
            prompt_name: Optional prompt file name (without .txt) to load.
            **kwargs: Additional CrewAI Agent parameters.
        """
        # Get OpenRouter API key
        api_key = config.get_api_key("openrouter")
        if not api_key:
            raise ValueError("OpenRouter API key not configured")
        
        # Get model from config or use provided
        agent_model = model or config.get_config().models.agent_model
        
        # Load system prompt if specified
        system_prompt = None
        if prompt_name:
            try:
                prompt_loader = PromptLoader()
                # Load base agent prompt
                base_prompt = prompt_loader.load("agents", "base_agent")
                # Load agent-specific prompt
                agent_prompt = prompt_loader.load("agents", prompt_name)
                # Combine prompts
                system_prompt = f"{base_prompt}\n\n{agent_prompt}"
            except Exception as e:
                # Log but don't fail - use default behavior
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to load prompt {prompt_name}: {e}")
        
        # Create LLM using CrewAI's LLM class with OpenRouter
        # CrewAI's LLM uses LiteLLM under the hood for OpenRouter support
        # For LiteLLM with OpenRouter, model format should be: openrouter/<provider>/<model>
        # If agent_model is already in openrouter/ format, use it; otherwise prepend openrouter/
        if agent_model.startswith("openrouter/"):
            model_name = agent_model
        else:
            # Format: openrouter/<provider>/<model> (e.g., openrouter/deepseek/deepseek-r1)
            model_name = f"openrouter/{agent_model}"
        
        llm = LLM(
            model=model_name,
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        # Enhance backstory with system prompt if available
        enhanced_backstory = backstory
        if system_prompt:
            enhanced_backstory = f"{backstory}\n\n## System Guidelines\n{system_prompt}"
        
        # Initialize CrewAI Agent
        super().__init__(
            role=role,
            goal=goal,
            backstory=enhanced_backstory,
            llm=llm,
            verbose=True,
            allow_delegation=False,
            **kwargs,
        )
        
        # Store metadata in a way compatible with Pydantic models
        # Use object.__setattr__ to bypass Pydantic validation for metadata
        object.__setattr__(self, "_omnidev_config", config)
        object.__setattr__(self, "_omnidev_agent_model", agent_model)
        object.__setattr__(self, "_omnidev_system_prompt", system_prompt)
    
    def __getattribute__(self, name: str) -> Any:
        """Override to handle custom attributes before Pydantic intercepts."""
        if name == "config":
            return object.__getattribute__(self, "_omnidev_config")
        elif name == "agent_model":
            return object.__getattribute__(self, "_omnidev_agent_model")
        elif name == "system_prompt":
            return object.__getattribute__(self, "_omnidev_system_prompt")
        # For all other attributes, use normal Pydantic behavior
        return super().__getattribute__(name)

