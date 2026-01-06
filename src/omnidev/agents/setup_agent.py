"""
Setup Agent for OmniDev.

Handles first-time setup, configuration, and onboarding.
"""

from pathlib import Path
from typing import Any

from omnidev.agents.base import BaseOmniDevAgent
from omnidev.core.config import ConfigManager


class SetupAgent(BaseOmniDevAgent):
    """Agent responsible for setup and configuration."""

    def __init__(self, config: ConfigManager) -> None:
        """Initialize setup agent.

        Args:
            config: ConfigManager instance.
        """
        super().__init__(
            role="Setup and Configuration Specialist",
            goal="Guide users through initial setup, configure API keys, validate settings, and ensure OmniDev is properly configured for optimal use",
            backstory="""You are a helpful onboarding specialist who makes setup processes 
            smooth and intuitive. You understand the importance of proper configuration 
            and guide users step-by-step through the setup wizard. You validate all 
            inputs and provide clear feedback.""",
            config=config,
            prompt_name="setup_agent",
        )
        # Config is already stored in BaseOmniDevAgent, no need to set again

    def run_setup_wizard(self) -> dict[str, Any]:
        """Run the setup wizard.

        Returns:
            Setup result dictionary.
        """
        # Setup wizard logic would go here
        # For now, return basic structure
        return {
            "status": "completed",
            "steps_completed": [],
            "next_steps": [],
        }

