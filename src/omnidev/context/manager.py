"""
Context manager for OmniDev.

Orchestrates file indexing, relevance scoring, and context building
to provide intelligent context selection for AI operations.
"""

from pathlib import Path
from typing import Optional

from omnidev.core.config import ConfigManager, ProjectConfig
from omnidev.core.exceptions import ContextError
from omnidev.core.logger import get_logger
from omnidev.context.builder import ContextBuilder
from omnidev.context.indexer import FileIndexer
from omnidev.context.scorer import RelevanceScorer


class ContextManager:
    """Manages project context for AI operations."""

    def __init__(
        self,
        project_root: Path,
        config: Optional[ConfigManager] = None,
    ) -> None:
        """Initialize the context manager.

        Args:
            project_root: Root directory of the project.
            config: Optional configuration manager.
        """
        self.project_root = project_root.resolve()
        self.config = config
        self.logger = get_logger("context")

        # Get context configuration
        context_config = self._get_context_config()

        # Initialize components
        exclude_patterns = set(context_config.exclude)
        self.indexer = FileIndexer(self.project_root, exclude_patterns)
        self.scorer = RelevanceScorer(self.indexer)
        self.builder = ContextBuilder(
            self.indexer,
            self.scorer,
            max_tokens=context_config.max_tokens,
        )

        # Index project on initialization
        self._index_project()

    def _get_context_config(self) -> "ContextConfig":
        """Get context configuration from config manager.

        Returns:
            ContextConfig instance.
        """
        if self.config:
            project_config = self.config.get_config()
            return project_config.context
        else:
            # Use defaults
            from omnidev.core.config import ContextConfig
            return ContextConfig()

    def _index_project(self) -> None:
        """Index the project files."""
        try:
            self.indexer.index_project()
            self.logger.info(f"Indexed {len(self.indexer.index)} files")
        except Exception as e:
            self.logger.warning(f"Failed to index project: {e}")

    def get_context(
        self,
        query: str,
        explicit_files: Optional[list[Path]] = None,
        use_summaries: bool = False,
    ) -> dict[str, str]:
        """Get context for a query.

        Args:
            query: Query or task description.
            explicit_files: Files explicitly mentioned.
            use_summaries: Whether to use summaries for low-priority files.

        Returns:
            Dictionary mapping file paths to contents.

        Raises:
            ContextError: If context building fails.
        """
        try:
            # Update index if needed
            if explicit_files:
                for file_path in explicit_files:
                    if file_path.exists():
                        self.indexer.update_file(file_path)

            # Build context
            if use_summaries:
                context = self.builder.build_summarized_context(query, explicit_files)
            else:
                context = self.builder.build_context(query, explicit_files)

            stats = self.builder.get_context_stats(context)
            self.logger.debug(f"Built context: {stats['files']} files, {stats['tokens']} tokens")

            return context
        except Exception as e:
            raise ContextError(f"Failed to build context: {e}") from e

    def update_file(self, file_path: Path) -> None:
        """Update index for a specific file.

        Args:
            file_path: Path to the file to update.
        """
        self.indexer.update_file(file_path)

    def add_focus_file(self, file_path: Path) -> None:
        """Add a file to the focus set.

        Args:
            file_path: Path to add to focus.
        """
        self.scorer.add_focus_file(file_path)

    def refresh_index(self) -> None:
        """Refresh the entire project index."""
        self._index_project()

    def get_file_metadata(self, file_path: Path) -> Optional["FileMetadata"]:
        """Get metadata for a file.

        Args:
            file_path: Path to the file.

        Returns:
            FileMetadata if found, None otherwise.
        """
        return self.indexer.get_file_metadata(file_path)

    def get_dependencies(self, file_path: Path) -> list[Path]:
        """Get files that a file depends on.

        Args:
            file_path: Path to the file.

        Returns:
            List of dependent file paths.
        """
        return self.indexer.get_dependencies(file_path)

