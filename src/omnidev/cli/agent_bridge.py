"""
CLI-Agent bridge for routing commands to agents.

Bridges between CLI commands and CrewAI agent system.
"""

from pathlib import Path
from typing import Any, Optional

from omnidev.agents.crews import OmniDevCrews
from omnidev.agents.manager import AgentManager
from omnidev.context.manager import ContextManager
from omnidev.core.config import ConfigManager
from omnidev.core.exceptions import OmniDevError
from omnidev.models.registry import ProviderRegistry


class CLIAgentBridge:
    """Bridge between CLI and agent system."""

    def __init__(
        self,
        config: ConfigManager,
        project_root: Path,
        context_manager: ContextManager,
        provider_registry: ProviderRegistry,
    ) -> None:
        """Initialize CLI-agent bridge.

        Args:
            config: ConfigManager instance.
            project_root: Project root directory.
            context_manager: ContextManager instance.
            provider_registry: ProviderRegistry instance.
        """
        self.config = config
        self.project_root = project_root
        self.agent_manager = AgentManager(config)
        self.crews_manager = OmniDevCrews(
            config, project_root, context_manager, provider_registry
        )
        
        # Register crews
        self.agent_manager.register_crew(
            "code_generation", self.crews_manager.create_code_generation_crew()
        )
        self.agent_manager.register_crew(
            "file_operations", self.crews_manager.create_file_operation_crew()
        )

    async def execute_query(self, query: str, mode: str = "auto") -> dict[str, Any]:
        """Execute a query using agents.

        Args:
            query: User query.
            mode: Operational mode.

        Returns:
            Execution result dictionary.
        """
        try:
            # Route to appropriate crew based on query type
            if self._is_file_operation(query):
                crew_name = "file_operations"
            else:
                crew_name = "code_generation"
            
            result = await self.agent_manager.execute_crew(crew_name, query)
            
            return {
                "success": True,
                "response": str(result),
                "crew": crew_name,
            }
        except OmniDevError as e:
            return {
                "success": False,
                "error": e.message,
                "response": f"Error: {e.message}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Unexpected error: {e}",
            }

    def _is_file_operation(self, query: str) -> bool:
        """Check if query is a file operation.

        Args:
            query: User query.

        Returns:
            True if query appears to be a file operation.
        """
        file_keywords = ["create", "delete", "edit", "update", "write", "file", "remove"]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in file_keywords)

