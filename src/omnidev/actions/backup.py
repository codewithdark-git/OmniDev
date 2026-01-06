"""
Backup system for OmniDev.

Provides automatic backup creation, session-based organization,
backup restoration, and retention policies.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from omnidev.core.exceptions import FileOperationError
from omnidev.core.logger import get_logger
from omnidev.core.session import SessionManager


class BackupManager:
    """Manages file backups for safe operations."""

    BACKUP_DIR_NAME = "backups"
    RETENTION_DAYS = 7
    MAX_SESSIONS = 10

    def __init__(self, project_root: Path, session_manager: Optional[SessionManager] = None) -> None:
        """Initialize the backup manager.

        Args:
            project_root: Root directory of the project.
            session_manager: Optional session manager for session-based backups.
        """
        self.project_root = project_root.resolve()
        self.session_manager = session_manager
        self.logger = get_logger("backup")

        # Setup backup directory
        self.backup_root = self.project_root / ".omnidev" / self.BACKUP_DIR_NAME
        self.backup_root.mkdir(parents=True, exist_ok=True)

        # Current session backup directory
        self.current_session_dir: Optional[Path] = None
        if session_manager and session_manager.current_session:
            self.current_session_dir = self.backup_root / f"session_{session_manager.current_session.session_id}"
            self.current_session_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, file_path: Path) -> Optional[Path]:
        """Create a backup of a file before modification.

        Args:
            file_path: Path to the file to backup.

        Returns:
            Path to backup file if created, None if file doesn't exist.

        Raises:
            FileOperationError: If backup creation fails.
        """
        if not file_path.exists():
            return None

        try:
            # Determine backup location
            if self.current_session_dir:
                backup_dir = self.current_session_dir
            else:
                # Create timestamped backup directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = self.backup_root / timestamp
                backup_dir.mkdir(parents=True, exist_ok=True)

            # Create backup file path
            rel_path = file_path.relative_to(self.project_root)
            backup_path = backup_dir / f"{rel_path.as_posix().replace('/', '_')}.backup"

            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file to backup
            shutil.copy2(file_path, backup_path)

            self.logger.debug(f"Created backup: {file_path} -> {backup_path}")
            return backup_path
        except Exception as e:
            raise FileOperationError(f"Failed to create backup for {file_path}: {e}") from e

    def restore_backup(self, backup_path: Path, destination: Optional[Path] = None) -> Path:
        """Restore a file from backup.

        Args:
            backup_path: Path to the backup file.
            destination: Optional destination path. If None, tries to infer from backup name.

        Returns:
            Path to restored file.

        Raises:
            FileOperationError: If restoration fails.
        """
        if not backup_path.exists():
            raise FileOperationError(f"Backup file does not exist: {backup_path}")

        try:
            # Determine destination
            if destination is None:
                # Try to infer from backup filename
                backup_name = backup_path.stem.replace(".backup", "")
                # Convert back to relative path
                parts = backup_name.split("_")
                destination = self.project_root / Path(*parts)
            else:
                destination = destination.resolve()

            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Restore file
            shutil.copy2(backup_path, destination)

            self.logger.info(f"Restored backup: {backup_path} -> {destination}")
            return destination
        except Exception as e:
            raise FileOperationError(f"Failed to restore backup: {e}") from e

    def list_backups(self, file_path: Optional[Path] = None) -> list[Path]:
        """List available backups.

        Args:
            file_path: Optional file path to filter backups for.

        Returns:
            List of backup file paths.
        """
        backups: list[Path] = []

        # Search all session directories
        for session_dir in self.backup_root.iterdir():
            if not session_dir.is_dir():
                continue

            if file_path:
                # Filter by file path
                rel_path = file_path.relative_to(self.project_root)
                backup_name = f"{rel_path.as_posix().replace('/', '_')}.backup"
                backup_file = session_dir / backup_name
                if backup_file.exists():
                    backups.append(backup_file)
            else:
                # List all backups in session
                backups.extend(session_dir.glob("*.backup"))

        # Sort by modification time (newest first)
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return backups

    def get_latest_backup(self, file_path: Path) -> Optional[Path]:
        """Get the latest backup for a file.

        Args:
            file_path: Path to the file.

        Returns:
            Path to latest backup if found, None otherwise.
        """
        backups = self.list_backups(file_path)
        return backups[0] if backups else None

    def cleanup_old_backups(self, days: Optional[int] = None) -> int:
        """Clean up old backup files.

        Args:
            days: Number of days to keep backups. If None, uses default retention.

        Returns:
            Number of backup files deleted.
        """
        retention_days = days or self.RETENTION_DAYS
        cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
        deleted_count = 0

        # Clean up old session directories
        session_dirs = sorted(
            [d for d in self.backup_root.iterdir() if d.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        # Keep only recent sessions
        for i, session_dir in enumerate(session_dirs):
            if i >= self.MAX_SESSIONS or session_dir.stat().st_mtime < cutoff_time:
                try:
                    shutil.rmtree(session_dir)
                    deleted_count += 1
                    self.logger.info(f"Deleted old backup session: {session_dir}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete backup session {session_dir}: {e}")

        return deleted_count

    def set_session(self, session_id: str) -> None:
        """Set the current session for session-based backups.

        Args:
            session_id: Session ID.
        """
        self.current_session_dir = self.backup_root / f"session_{session_id}"
        self.current_session_dir.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Set backup session: {session_id}")

