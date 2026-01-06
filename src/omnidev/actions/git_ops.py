"""
Git integration for OmniDev.

Provides Git repository detection, auto-commit functionality,
smart commit message generation, branch management, and rollback support.
"""

from pathlib import Path
from typing import Optional

try:
    import git
except ImportError:
    git = None  # type: ignore

from omnidev.core.exceptions import FileOperationError
from omnidev.core.logger import get_logger


class GitOperations:
    """Handles Git operations for version control."""

    def __init__(self, project_root: Path) -> None:
        """Initialize Git operations.

        Args:
            project_root: Root directory of the project.

        Raises:
            FileOperationError: If Git repository cannot be accessed.
        """
        self.project_root = project_root.resolve()
        self.logger = get_logger("git")

        if git is None:
            self.repo = None
            self.logger.warning("GitPython not installed - Git operations disabled")
            return

        try:
            self.repo = git.Repo(self.project_root, search_parent_directories=True)
            self.logger.info(f"Initialized Git operations for: {self.repo.working_dir}")
        except git.InvalidGitRepositoryError:
            self.repo = None
            self.logger.warning("Not a Git repository - Git operations disabled")
        except Exception as e:
            self.repo = None
            self.logger.warning(f"Failed to initialize Git: {e}")

    def is_git_repo(self) -> bool:
        """Check if project is a Git repository.

        Returns:
            True if Git repository, False otherwise.
        """
        return self.repo is not None

    def get_current_branch(self) -> Optional[str]:
        """Get current Git branch name.

        Returns:
            Branch name if in Git repo, None otherwise.
        """
        if not self.repo:
            return None

        try:
            return self.repo.active_branch.name
        except Exception:
            return None

    def create_branch(self, branch_name: str, checkout: bool = True) -> Optional[str]:
        """Create a new Git branch.

        Args:
            branch_name: Name of the branch to create.
            checkout: Whether to checkout the new branch.

        Returns:
            Branch name if created, None otherwise.

        Raises:
            FileOperationError: If branch creation fails.
        """
        if not self.repo:
            raise FileOperationError("Not a Git repository")

        try:
            # Check if branch already exists
            if branch_name in [ref.name for ref in self.repo.heads]:
                if checkout:
                    self.repo.heads[branch_name].checkout()
                return branch_name

            # Create new branch
            new_branch = self.repo.create_head(branch_name)
            if checkout:
                new_branch.checkout()

            self.logger.info(f"Created branch: {branch_name}")
            return branch_name
        except Exception as e:
            raise FileOperationError(f"Failed to create branch {branch_name}: {e}") from e

    def get_changed_files(self) -> list[Path]:
        """Get list of changed files in working directory.

        Returns:
            List of changed file paths.
        """
        if not self.repo:
            return []

        try:
            changed_files = []
            for item in self.repo.index.diff(None):
                if item.a_path:
                    changed_files.append(self.project_root / item.a_path)
            for item in self.repo.untracked_files:
                changed_files.append(self.project_root / item)
            return changed_files
        except Exception:
            return []

    def generate_commit_message(self, files: list[Path], operation: str = "update") -> str:
        """Generate a smart commit message based on changes.

        Args:
            files: List of changed files.
            operation: Type of operation (create, update, delete).

        Returns:
            Generated commit message.
        """
        if not files:
            return f"{operation}: No files changed"

        # Analyze file types and generate message
        file_count = len(files)
        if file_count == 1:
            file_name = files[0].name
            return f"{operation}: {file_name}"
        else:
            # Group by file type
            extensions: dict[str, int] = {}
            for file_path in files:
                ext = file_path.suffix or "no extension"
                extensions[ext] = extensions.get(ext, 0) + 1

            # Generate summary
            if len(extensions) == 1:
                ext = list(extensions.keys())[0]
                return f"{operation}: {file_count} {ext} files"
            else:
                return f"{operation}: {file_count} files"

    def commit_changes(
        self,
        message: Optional[str] = None,
        files: Optional[list[Path]] = None,
        auto_stage: bool = True,
    ) -> Optional[str]:
        """Commit changes to Git repository.

        Args:
            message: Commit message. If None, generates one.
            files: Optional list of files to commit. If None, commits all changes.
            auto_stage: Whether to automatically stage files.

        Returns:
            Commit hash if successful, None otherwise.

        Raises:
            FileOperationError: If commit fails.
        """
        if not self.repo:
            raise FileOperationError("Not a Git repository")

        try:
            # Stage files
            if auto_stage:
                if files:
                    # Stage specific files
                    for file_path in files:
                        rel_path = file_path.relative_to(self.project_root)
                        self.repo.index.add([str(rel_path)])
                else:
                    # Stage all changes
                    self.repo.index.add(self.repo.untracked_files)
                    self.repo.index.add([item.a_path for item in self.repo.index.diff(None)])

            # Generate commit message if not provided
            if not message:
                changed = self.get_changed_files()
                message = self.generate_commit_message(changed)

            # Check if there are changes to commit
            if not self.repo.is_dirty() and not self.repo.untracked_files:
                self.logger.debug("No changes to commit")
                return None

            # Create commit
            commit = self.repo.index.commit(message)
            self.logger.info(f"Created commit: {commit.hexsha[:8]} - {message}")
            return commit.hexsha
        except Exception as e:
            raise FileOperationError(f"Failed to commit changes: {e}") from e

    def rollback_to_commit(self, commit_hash: str) -> None:
        """Rollback to a specific commit.

        Args:
            commit_hash: Commit hash to rollback to.

        Raises:
            FileOperationError: If rollback fails.
        """
        if not self.repo:
            raise FileOperationError("Not a Git repository")

        try:
            commit = self.repo.commit(commit_hash)
            self.repo.head.reset(commit=commit, index=True, working_tree=True)
            self.logger.info(f"Rolled back to commit: {commit_hash[:8]}")
        except Exception as e:
            raise FileOperationError(f"Failed to rollback to commit {commit_hash}: {e}") from e

    def get_recent_commits(self, limit: int = 10) -> list[dict[str, str]]:
        """Get recent commit history.

        Args:
            limit: Maximum number of commits to return.

        Returns:
            List of commit dictionaries with hash, message, and author.
        """
        if not self.repo:
            return []

        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=limit):
                commits.append({
                    "hash": commit.hexsha,
                    "message": commit.message.strip(),
                    "author": commit.author.name,
                    "date": commit.committed_datetime.isoformat(),
                })
            return commits
        except Exception:
            return []

    def get_file_history(self, file_path: Path, limit: int = 10) -> list[dict[str, str]]:
        """Get commit history for a specific file.

        Args:
            file_path: Path to the file.
            limit: Maximum number of commits to return.

        Returns:
            List of commit dictionaries.
        """
        if not self.repo:
            return []

        try:
            rel_path = file_path.relative_to(self.project_root)
            commits = []
            for commit in self.repo.iter_commits(paths=str(rel_path), max_count=limit):
                commits.append({
                    "hash": commit.hexsha,
                    "message": commit.message.strip(),
                    "author": commit.author.name,
                    "date": commit.committed_datetime.isoformat(),
                })
            return commits
        except Exception:
            return []

