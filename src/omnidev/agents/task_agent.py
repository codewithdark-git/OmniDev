"""
Task Agent for OmniDev.

Handles task decomposition and planning.
"""

from typing import Any, Optional

from omnidev.agents.base import BaseOmniDevAgent
from omnidev.core.config import ConfigManager


class TaskAgent(BaseOmniDevAgent):
    """Agent responsible for task decomposition and planning."""

    def __init__(self, config: ConfigManager) -> None:
        """Initialize task agent.

        Args:
            config: ConfigManager instance.
        """
        super().__init__(
            role="Task Planning and Decomposition Specialist",
            goal="Break down complex tasks into manageable steps, create execution plans, and coordinate task execution",
            backstory="""You are an expert project manager who excels at breaking down 
            complex software development tasks into clear, actionable steps. You understand 
            dependencies, sequencing, and resource requirements. You create detailed plans 
            that ensure successful task completion.""",
            config=config,
            prompt_name="task_agent",
        )

    def decompose_task(self, task: str) -> dict[str, Any]:
        """Decompose a task into steps.

        Args:
            task: Task description.

        Returns:
            Task decomposition dictionary with steps.
        """
        # Use agent to decompose task
        return {
            "task": task,
            "steps": [],
            "estimated_complexity": "medium",
            "dependencies": [],
        }

