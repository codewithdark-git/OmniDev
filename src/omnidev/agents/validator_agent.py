"""
Validator Agent for OmniDev.

Handles code validation and quality checks.
"""

from typing import Any, Optional
from pathlib import Path

from omnidev.actions.validator import CodeValidator
from omnidev.agents.base import BaseOmniDevAgent
from omnidev.core.config import ConfigManager


class ValidatorAgent(BaseOmniDevAgent):
    """Agent responsible for code validation."""

    def __init__(self, config: ConfigManager, project_root: Path) -> None:
        """Initialize validator agent.

        Args:
            config: ConfigManager instance.
            project_root: Project root directory.
        """
        super().__init__(
            role="Code Quality and Validation Specialist",
            goal="Validate code for syntax errors, import issues, and quality problems, providing actionable feedback for improvements",
            backstory="""You are a meticulous code reviewer with deep knowledge of 
            programming languages, best practices, and common pitfalls. You catch 
            errors before they cause problems and provide clear, helpful feedback 
            for code improvements.""",
            config=config,
            prompt_name="validator_agent",
        )
        object.__setattr__(self, "_omnidev_validator", CodeValidator(project_root))
        object.__setattr__(self, "_omnidev_project_root", project_root)
    
    @property
    def validator(self) -> CodeValidator:
        """Get CodeValidator instance."""
        return getattr(self, "_omnidev_validator", None)
    
    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        return getattr(self, "_omnidev_project_root", None)

    def validate_code(self, file_path: Path) -> dict[str, Any]:
        """Validate code in a file.

        Args:
            file_path: Path to file to validate.

        Returns:
            Validation result dictionary.
        """
        result = self.validator.validate_file(file_path)
        return {
            "valid": result.get("valid", False),
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
        }

