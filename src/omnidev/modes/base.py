"""
Base mode framework for OmniDev operational modes.

Provides common functionality and abstract interface for all modes.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from omnidev.actions.backup import BackupManager
from omnidev.actions.file_ops import FileOperations
from omnidev.actions.git_ops import GitOperations
from omnidev.actions.validator import CodeValidator
from omnidev.context.manager import ContextManager
from omnidev.core.config import ConfigManager
from omnidev.core.exceptions import OmniDevError
from omnidev.core.logger import get_logger
from omnidev.core.session import SessionManager
from omnidev.models.router import ModelRouter


class BaseMode(ABC):
    """Abstract base class for all operational modes."""

    def __init__(
        self,
        project_root: Path,
        config: ConfigManager,
        session_manager: SessionManager,
        context_manager: ContextManager,
        model_router: ModelRouter,
    ) -> None:
        """Initialize the base mode.

        Args:
            project_root: Root directory of the project.
            config: Configuration manager.
            session_manager: Session manager.
            context_manager: Context manager.
            model_router: Model router.
        """
        self.project_root = project_root.resolve()
        self.config = config
        self.session_manager = session_manager
        self.context_manager = context_manager
        self.model_router = model_router
        self.logger = get_logger(f"mode.{self.__class__.__name__.lower()}")

        # Initialize action components
        self.file_ops = FileOperations(self.project_root)
        self.backup_manager = BackupManager(self.project_root, session_manager)
        self.git_ops = GitOperations(self.project_root)
        self.validator = CodeValidator(self.project_root)

    def get_configured_provider(self) -> Optional[str]:
        """Get the configured provider from settings.
        
        Returns:
            Provider name or None if not configured.
        """
        try:
            cfg = self.config.get_config()
            return cfg.models.fallback
        except Exception:
            return None

    def get_configured_model(self) -> Optional[str]:
        """Get the configured model from settings.
        
        Returns:
            Model name or None if not configured.
        """
        try:
            cfg = self.config.get_config()
            return cfg.models.preferred
        except Exception:
            return None

    @abstractmethod
    async def execute(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a query in this mode.

        Args:
            query: User query or task description.
            **kwargs: Mode-specific parameters.

        Returns:
            Dictionary with execution results.

        Raises:
            OmniDevError: If execution fails.
        """
        pass

    def get_context(self, query: str, explicit_files: Optional[list[Path]] = None) -> dict[str, str]:
        """Get context for a query.

        Args:
            query: Query string.
            explicit_files: Files explicitly mentioned.

        Returns:
            Context dictionary.
        """
        return self.context_manager.get_context(query, explicit_files)

    def create_file_safe(self, file_path: Path, content: str, create_backup: bool = True) -> Path:
        """Safely create a file with backup.

        Args:
            file_path: Path to the file.
            content: Content to write.
            create_backup: Whether to create backup first.

        Returns:
            Path to created file.

        Raises:
            OmniDevError: If file creation fails.
        """
        try:
            # Validate content
            self.validator.pre_write_validation(file_path, content)

            # Create backup if file exists
            if file_path.exists() and create_backup:
                self.backup_manager.create_backup(file_path)

            # Create file
            created_path = self.file_ops.create_file(file_path, content, overwrite=True)

            # Log to session
            self.session_manager.add_file_change("create", created_path, success=True)

            return created_path
        except Exception as e:
            self.logger.error(f"Failed to create file {file_path}: {e}")
            self.session_manager.add_file_change("create", file_path, success=False)
            raise OmniDevError(f"Failed to create file: {e}") from e

    def update_file_safe(self, file_path: Path, content: str) -> Path:
        """Safely update a file with backup.

        Args:
            file_path: Path to the file.
            content: New content.

        Returns:
            Path to updated file.

        Raises:
            OmniDevError: If file update fails.
        """
        try:
            # Validate content
            self.validator.pre_write_validation(file_path, content)

            # Create backup
            backup_path = self.backup_manager.create_backup(file_path)

            # Update file
            updated_path = self.file_ops.update_file(file_path, content)

            # Log to session
            self.session_manager.add_file_change("edit", updated_path, backup_path, success=True)

            return updated_path
        except Exception as e:
            self.logger.error(f"Failed to update file {file_path}: {e}")
            self.session_manager.add_file_change("edit", file_path, success=False)
            raise OmniDevError(f"Failed to update file: {e}") from e

    def delete_file_safe(self, file_path: Path, require_confirmation: bool = True) -> None:
        """Safely delete a file with backup.

        Args:
            file_path: Path to the file.
            require_confirmation: Whether to require confirmation (mode-specific).

        Raises:
            OmniDevError: If file deletion fails.
        """
        try:
            # Create backup
            backup_path = self.backup_manager.create_backup(file_path)

            # Delete file
            self.file_ops.delete_file(file_path)

            # Log to session
            self.session_manager.add_file_change("delete", file_path, backup_path, success=True)
        except Exception as e:
            self.logger.error(f"Failed to delete file {file_path}: {e}")
            self.session_manager.add_file_change("delete", file_path, success=False)
            raise OmniDevError(f"Failed to delete file: {e}") from e

    def commit_changes(self, message: Optional[str] = None, files: Optional[list[Path]] = None) -> Optional[str]:
        """Commit changes to Git.

        Args:
            message: Optional commit message.
            files: Optional list of files to commit.

        Returns:
            Commit hash if successful, None otherwise.
        """
        if not self.git_ops.is_git_repo():
            return None

        try:
            return self.git_ops.commit_changes(message, files)
        except Exception as e:
            self.logger.warning(f"Failed to commit changes: {e}")
            return None

