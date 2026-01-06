"""
File Processing Agent for OmniDev.

Handles all file operations with intelligent decision-making using OpenRouter.
"""

from pathlib import Path
from typing import Any, Optional

from omnidev.actions.file_ops import FileOperations
from omnidev.agents.base import BaseOmniDevAgent
from omnidev.core.config import ConfigManager


class FileProcessingAgent(BaseOmniDevAgent):
    """Agent responsible for file operations."""

    def __init__(self, config: ConfigManager, project_root: Path) -> None:
        """Initialize file processing agent.

        Args:
            config: ConfigManager instance.
            project_root: Project root directory.
        """
        super().__init__(
            role="File Operations Specialist",
            goal="Safely and intelligently handle all file operations including creation, reading, updating, and deletion with proper validation and backup coordination",
            backstory="""You are an expert file system manager with deep understanding of 
            software project structures. You always prioritize safety, validation, and 
            maintainability when performing file operations. You coordinate with backup 
            systems and ensure no critical files are accidentally modified or deleted.""",
            config=config,
            prompt_name="file_agent",
        )
        object.__setattr__(self, "_omnidev_file_ops", FileOperations(project_root))
        object.__setattr__(self, "_omnidev_project_root", project_root)
    
    @property
    def file_ops(self) -> FileOperations:
        """Get FileOperations instance."""
        return getattr(self, "_omnidev_file_ops", None)
    
    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        return getattr(self, "_omnidev_project_root", None)

    def should_create_file(self, file_path: Path, content: str) -> dict[str, Any]:
        """Determine if a file should be created.

        Args:
            file_path: Path to the file.
            content: File content.

        Returns:
            Decision dictionary with 'should_create' and 'reason'.
        """
        # Use agent reasoning for complex decisions
        # For now, basic validation
        if file_path.exists():
            return {"should_create": False, "reason": "File already exists"}
        return {"should_create": True, "reason": "File can be created"}

