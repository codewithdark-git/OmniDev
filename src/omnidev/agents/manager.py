"""
Agent Manager for OmniDev.

Manages agent lifecycle, orchestration, and resource pooling.
"""

from typing import Any, Optional

from omnidev.core.config import ConfigManager
from omnidev.core.exceptions import OmniDevError


class AgentManager:
    """Manages CrewAI agents for OmniDev."""

    def __init__(self, config: ConfigManager) -> None:
        """Initialize agent manager.

        Args:
            config: ConfigManager instance.
        """
        self.config = config
        self.agents: dict[str, Any] = {}
        self.crews: dict[str, Any] = {}

    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Get an agent by name.

        Args:
            agent_name: Name of the agent.

        Returns:
            Agent instance if found, None otherwise.
        """
        return self.agents.get(agent_name)

    def register_agent(self, name: str, agent: Any) -> None:
        """Register an agent.

        Args:
            name: Agent name.
            agent: Agent instance.
        """
        self.agents[name] = agent

    def register_crew(self, name: str, crew: Any) -> None:
        """Register a crew.

        Args:
            name: Crew name.
            crew: Crew instance.
        """
        self.crews[name] = crew

    def get_crew(self, crew_name: str) -> Optional[Any]:
        """Get a crew by name.

        Args:
            crew_name: Name of the crew.

        Returns:
            Crew instance if found, None otherwise.
        """
        return self.crews.get(crew_name)

    async def execute_crew(self, crew_name: str, task: str, **kwargs: Any) -> Any:
        """Execute a crew with a task.

        Args:
            crew_name: Name of the crew to execute.
            task: Task description.
            **kwargs: Additional parameters.

        Returns:
            Crew execution result.

        Raises:
            OmniDevError: If crew not found or execution fails.
        """
        crew = self.get_crew(crew_name)
        if not crew:
            raise OmniDevError(f"Crew '{crew_name}' not found")
        
        try:
            result = crew.kickoff(inputs={"task": task, **kwargs})
            return result
        except Exception as e:
            raise OmniDevError(f"Crew execution failed: {e}") from e

