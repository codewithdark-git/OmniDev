"""
Session management for OmniDev.

Handles session creation, state persistence, undo/redo capability,
and session history tracking.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from omnidev.core.config import ConfigManager
from omnidev.core.exceptions import ConfigurationError
from omnidev.core.logger import LoggerManager, get_logger


class SessionState:
    """Represents the state of a session."""

    def __init__(
        self,
        session_id: str,
        project_root: Path,
        created_at: Optional[datetime] = None,
    ) -> None:
        """Initialize session state.

        Args:
            session_id: Unique session identifier.
            project_root: Root directory of the project.
            created_at: Session creation timestamp.
        """
        self.session_id = session_id
        self.project_root = project_root
        self.created_at = created_at or datetime.now()
        self.last_updated = self.created_at
        self.commands: list[dict[str, Any]] = []
        self.file_changes: list[dict[str, Any]] = []
        self.model_usage: list[dict[str, Any]] = []
        self.undo_stack: list[dict[str, Any]] = []
        self.redo_stack: list[dict[str, Any]] = []

    def to_dict(self) -> dict[str, Any]:
        """Convert session state to dictionary.

        Returns:
            Dictionary representation of session state.
        """
        return {
            "session_id": self.session_id,
            "project_root": str(self.project_root),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "commands": self.commands,
            "file_changes": self.file_changes,
            "model_usage": self.model_usage,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionState":
        """Create session state from dictionary.

        Args:
            data: Dictionary containing session state.

        Returns:
            SessionState instance.

        Raises:
            ConfigurationError: If data is invalid.
        """
        try:
            session = cls(
                session_id=data["session_id"],
                project_root=Path(data["project_root"]),
                created_at=datetime.fromisoformat(data["created_at"]),
            )
            session.last_updated = datetime.fromisoformat(data["last_updated"])
            session.commands = data.get("commands", [])
            session.file_changes = data.get("file_changes", [])
            session.model_usage = data.get("model_usage", [])
            return session
        except (KeyError, ValueError) as e:
            raise ConfigurationError(f"Invalid session data: {e}") from e


class SessionManager:
    """Manages OmniDev sessions."""

    SESSION_DIR = Path.home() / ".omnidev" / "sessions"
    SESSION_FILE_PREFIX = "session_"
    SESSION_FILE_SUFFIX = ".json"

    def __init__(self, project_root: Path, config: Optional[ConfigManager] = None) -> None:
        """Initialize the session manager.

        Args:
            project_root: Root directory of the project.
            config: Optional configuration manager.

        Raises:
            ConfigurationError: If session directory cannot be created.
        """
        self.project_root = project_root
        self.config = config
        self.logger = get_logger("session")
        self.current_session: Optional[SessionState] = None

        try:
            self.SESSION_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ConfigurationError(f"Failed to create session directory: {e}") from e

    def create_session(self) -> SessionState:
        """Create a new session.

        Returns:
            New session state.
        """
        session_id = self._generate_session_id()
        session = SessionState(session_id=session_id, project_root=self.project_root)
        self.current_session = session
        self._save_session(session)
        self.logger.info(f"Created new session: {session_id}")
        return session

    def load_session(self, session_id: Optional[str] = None) -> Optional[SessionState]:
        """Load a session by ID or the most recent session.

        Args:
            session_id: Optional session ID. If None, loads most recent.

        Returns:
            Session state if found, None otherwise.

        Raises:
            ConfigurationError: If session file is invalid.
        """
        if session_id:
            session_file = self.SESSION_DIR / f"{self.SESSION_FILE_PREFIX}{session_id}{self.SESSION_FILE_SUFFIX}"
            if not session_file.exists():
                self.logger.warning(f"Session not found: {session_id}")
                return None
        else:
            # Find most recent session
            session_files = sorted(
                self.SESSION_DIR.glob(f"{self.SESSION_FILE_PREFIX}*{self.SESSION_FILE_SUFFIX}"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if not session_files:
                return None
            session_file = session_files[0]

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            session = SessionState.from_dict(data)
            self.current_session = session
            self.logger.info(f"Loaded session: {session.session_id}")
            return session
        except Exception as e:
            raise ConfigurationError(f"Failed to load session: {e}") from e

    def save_current_session(self) -> None:
        """Save the current session to disk.

        Raises:
            ConfigurationError: If no current session or save fails.
        """
        if not self.current_session:
            raise ConfigurationError("No current session to save")
        self._save_session(self.current_session)

    def add_command(self, command: str, mode: str, result: dict[str, Any]) -> None:
        """Add a command to the current session.

        Args:
            command: Command that was executed.
            mode: Operational mode used.
            result: Command result dictionary.
        """
        if not self.current_session:
            self.create_session()

        assert self.current_session is not None
        command_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "mode": mode,
            "result": result,
        }
        self.current_session.commands.append(command_entry)
        self.current_session.last_updated = datetime.now()
        self._save_session(self.current_session)

    def add_file_change(
        self,
        operation: str,
        file_path: Path,
        backup_path: Optional[Path] = None,
        success: bool = True,
    ) -> None:
        """Add a file change to the current session.

        Args:
            operation: Operation type (create, edit, delete).
            file_path: Path to the file.
            backup_path: Optional backup file path.
            success: Whether the operation succeeded.
        """
        if not self.current_session:
            self.create_session()

        assert self.current_session is not None
        change_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "file_path": str(file_path),
            "backup_path": str(backup_path) if backup_path else None,
            "success": success,
        }
        self.current_session.file_changes.append(change_entry)
        self.current_session.last_updated = datetime.now()
        self._save_session(self.current_session)

    def add_model_usage(self, provider: str, model: str, tokens: int, cost: float = 0.0) -> None:
        """Add model usage to the current session.

        Args:
            provider: Provider name.
            model: Model name.
            tokens: Number of tokens used.
            cost: Cost in USD.
        """
        if not self.current_session:
            self.create_session()

        assert self.current_session is not None
        usage_entry = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "tokens": tokens,
            "cost": cost,
        }
        self.current_session.model_usage.append(usage_entry)
        self.current_session.last_updated = datetime.now()
        self._save_session(self.current_session)

    def push_to_undo_stack(self, action: dict[str, Any]) -> None:
        """Push an action to the undo stack.

        Args:
            action: Action dictionary to push.
        """
        if not self.current_session:
            self.create_session()

        assert self.current_session is not None
        self.current_session.undo_stack.append(action)
        # Clear redo stack when new action is pushed
        self.current_session.redo_stack.clear()
        self._save_session(self.current_session)

    def pop_from_undo_stack(self) -> Optional[dict[str, Any]]:
        """Pop an action from the undo stack.

        Returns:
            Action dictionary if available, None otherwise.
        """
        if not self.current_session or not self.current_session.undo_stack:
            return None

        assert self.current_session is not None
        action = self.current_session.undo_stack.pop()
        self.current_session.redo_stack.append(action)
        self._save_session(self.current_session)
        return action

    def pop_from_redo_stack(self) -> Optional[dict[str, Any]]:
        """Pop an action from the redo stack.

        Returns:
            Action dictionary if available, None otherwise.
        """
        if not self.current_session or not self.current_session.redo_stack:
            return None

        assert self.current_session is not None
        action = self.current_session.redo_stack.pop()
        self.current_session.undo_stack.append(action)
        self._save_session(self.current_session)
        return action

    def get_session_history(self, limit: int = 10) -> list[SessionState]:
        """Get recent session history.

        Args:
            limit: Maximum number of sessions to return.

        Returns:
            List of recent session states.
        """
        session_files = sorted(
            self.SESSION_DIR.glob(f"{self.SESSION_FILE_PREFIX}*{self.SESSION_FILE_SUFFIX}"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:limit]

        sessions = []
        for session_file in session_files:
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                session = SessionState.from_dict(data)
                sessions.append(session)
            except Exception as e:
                self.logger.warning(f"Failed to load session from {session_file}: {e}")

        return sessions

    def _generate_session_id(self) -> str:
        """Generate a unique session ID.

        Returns:
            Session ID string.
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def _save_session(self, session: SessionState) -> None:
        """Save a session to disk.

        Args:
            session: Session state to save.

        Raises:
            ConfigurationError: If saving fails.
        """
        session_file = (
            self.SESSION_DIR / f"{self.SESSION_FILE_PREFIX}{session.session_id}{self.SESSION_FILE_SUFFIX}"
        )
        try:
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ConfigurationError(f"Failed to save session: {e}") from e

    def cleanup_old_sessions(self, days: int = 7) -> None:
        """Clean up session files older than specified days.

        Args:
            days: Number of days to keep sessions (default: 7).
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0

        for session_file in self.SESSION_DIR.glob(f"{self.SESSION_FILE_PREFIX}*{self.SESSION_FILE_SUFFIX}"):
            if session_file.stat().st_mtime < cutoff_time:
                try:
                    session_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to delete old session file {session_file}: {e}")

        if deleted_count > 0:
            self.logger.info(f"Cleaned up {deleted_count} old session file(s)")

