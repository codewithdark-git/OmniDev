"""
Context Agent for OmniDev.

Handles intelligent context building and file selection.
"""

from pathlib import Path
from typing import Any, Optional

from omnidev.agents.base import BaseOmniDevAgent
from omnidev.context.manager import ContextManager
from omnidev.core.config import ConfigManager


class ContextAgent(BaseOmniDevAgent):
    """Agent responsible for context management."""

    def __init__(self, config: ConfigManager, context_manager: ContextManager) -> None:
        """Initialize context agent.

        Args:
            config: ConfigManager instance.
            context_manager: ContextManager instance.
        """
        super().__init__(
            role="Context Management Specialist",
            goal="Intelligently select and organize relevant files for AI context, optimize token usage, and ensure the most important information is included",
            backstory="""You are an expert at understanding codebases and determining 
            which files are most relevant to a given task. You excel at balancing 
            context completeness with token efficiency, always including the most 
            important files while staying within token limits.""",
            config=config,
            prompt_name="context_agent",
        )
        object.__setattr__(self, "_omnidev_context_manager", context_manager)
    
    @property
    def context_manager(self) -> ContextManager:
        """Get ContextManager instance."""
        return getattr(self, "_omnidev_context_manager", None)

    def select_files(self, query: str, max_files: int = 50) -> list[Path]:
        """Select relevant files for a query.

        Args:
            query: User query.
            max_files: Maximum number of files to include.

        Returns:
            List of selected file paths.
        """
        # Use context manager to get context
        context = self.context_manager.get_context(query)
        # Context is a dict mapping file paths (as strings) to contents
        return [Path(path) for path in context.keys()]

