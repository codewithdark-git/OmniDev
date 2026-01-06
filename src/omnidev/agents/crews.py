"""
CrewAI crews for OmniDev workflows.

Defines crews for different task types and workflows.
"""

from pathlib import Path
from typing import Any, Optional

from crewai import Crew, Task

from omnidev.agents.context_agent import ContextAgent
from omnidev.agents.file_agent import FileProcessingAgent
from omnidev.agents.router_agent import RouterAgent
from omnidev.agents.task_agent import TaskAgent
from omnidev.agents.validator_agent import ValidatorAgent
from omnidev.context.manager import ContextManager
from omnidev.core.config import ConfigManager
from omnidev.models.registry import ProviderRegistry


class OmniDevCrews:
    """Crew definitions for OmniDev workflows."""

    def __init__(
        self,
        config: ConfigManager,
        project_root: Path,
        context_manager: ContextManager,
        provider_registry: ProviderRegistry,
    ) -> None:
        """Initialize crews.

        Args:
            config: ConfigManager instance.
            project_root: Project root directory.
            context_manager: ContextManager instance.
            provider_registry: ProviderRegistry instance.
        """
        self.config = config
        self.project_root = project_root
        self.context_manager = context_manager
        self.provider_registry = provider_registry
        
        # Initialize agents
        self.file_agent = FileProcessingAgent(config, project_root)
        self.context_agent = ContextAgent(config, context_manager)
        self.router_agent = RouterAgent(config, provider_registry)
        self.task_agent = TaskAgent(config)
        self.validator_agent = ValidatorAgent(config, project_root)

    def create_code_generation_crew(self) -> Crew:
        """Create crew for code generation tasks.

        Returns:
            Crew instance for code generation.
        """
        # Task: Decompose the user request
        decompose_task = Task(
            description="Analyze the user's request and break it down into actionable steps",
            agent=self.task_agent,
            expected_output="A structured plan with steps",
        )
        
        # Task: Select relevant context
        context_task = Task(
            description="Select the most relevant files for the task",
            agent=self.context_agent,
            expected_output="List of relevant file paths",
        )
        
        # Task: Select appropriate model
        routing_task = Task(
            description="Select the best AI model for code generation",
            agent=self.router_agent,
            expected_output="Model selection with reasoning",
        )
        
        # Create crew
        crew = Crew(
            agents=[self.task_agent, self.context_agent, self.router_agent],
            tasks=[decompose_task, context_task, routing_task],
            verbose=True,
        )
        
        return crew

    def create_file_operation_crew(self) -> Crew:
        """Create crew for file operations.

        Returns:
            Crew instance for file operations.
        """
        # Task: Validate file operation
        validation_task = Task(
            description="Validate that the file operation is safe and appropriate",
            agent=self.validator_agent,
            expected_output="Validation result",
        )
        
        # Task: Execute file operation
        file_task = Task(
            description="Execute the file operation safely",
            agent=self.file_agent,
            expected_output="File operation result",
        )
        
        crew = Crew(
            agents=[self.file_agent, self.validator_agent],
            tasks=[validation_task, file_task],
            verbose=True,
        )
        
        return crew

