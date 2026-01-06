"""
Logging system for OmniDev.

Provides structured logging with file and console handlers,
session-based log files, and error tracking.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from omnidev.core.config import ConfigManager


class OmniDevFormatter(logging.Formatter):
    """Custom formatter for OmniDev logs."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True) -> None:
        """Initialize the formatter.

        Args:
            use_colors: Whether to use ANSI colors in output.
        """
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record.

        Args:
            record: Log record to format.

        Returns:
            Formatted log message.
        """
        # Add color to level name if using colors
        if self.use_colors and record.levelname in self.COLORS:
            levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        else:
            levelname = record.levelname

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Format message
        message = f"[{timestamp}] [{levelname}] {record.getMessage()}"

        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


class LoggerManager:
    """Manages logging configuration for OmniDev."""

    LOG_DIR = Path.home() / ".omnidev" / "logs"
    AUDIT_LOG_FILE = "audit.log"
    SESSION_LOG_PREFIX = "session_"

    def __init__(self, config: Optional[ConfigManager] = None, session_id: Optional[str] = None) -> None:
        """Initialize the logger manager.

        Args:
            config: Configuration manager instance.
            session_id: Optional session ID for session-based logging.
        """
        self.config = config
        self.session_id = session_id or self._generate_session_id()
        self.logger = logging.getLogger("omnidev")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        # Remove existing handlers
        self.logger.handlers.clear()

        # Setup handlers
        self._setup_handlers()

    def _generate_session_id(self) -> str:
        """Generate a unique session ID.

        Returns:
            Session ID string.
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _setup_handlers(self) -> None:
        """Setup console and file handlers."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(OmniDevFormatter(use_colors=True))
        self.logger.addHandler(console_handler)

        # Ensure log directory exists
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Audit log handler (all logs)
        audit_log_path = self.LOG_DIR / self.AUDIT_LOG_FILE
        audit_handler = logging.FileHandler(audit_log_path, encoding="utf-8")
        audit_handler.setLevel(logging.DEBUG)
        audit_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        )
        self.logger.addHandler(audit_handler)

        # Session log handler (if session ID provided)
        if self.session_id:
            session_log_path = self.LOG_DIR / f"{self.SESSION_LOG_PREFIX}{self.session_id}.log"
            session_handler = logging.FileHandler(session_log_path, encoding="utf-8")
            session_handler.setLevel(logging.DEBUG)
            session_handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
            )
            self.logger.addHandler(session_handler)

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance.

        Args:
            name: Optional logger name. If None, returns the main logger.

        Returns:
            Logger instance.
        """
        if name:
            return logging.getLogger(f"omnidev.{name}")
        return self.logger

    def set_level(self, level: str) -> None:
        """Set the logging level.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

        Raises:
            ValueError: If level is invalid.
        """
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")

        self.logger.setLevel(numeric_level)
        for handler in self.logger.handlers:
            handler.setLevel(numeric_level)

    def log_file_operation(self, operation: str, file_path: Path, success: bool = True) -> None:
        """Log a file operation.

        Args:
            operation: Operation type (create, edit, delete).
            file_path: Path to the file.
            success: Whether the operation succeeded.
        """
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"File {operation.upper()}: {file_path} - {status}")

    def log_model_usage(self, provider: str, model: str, tokens: int, cost: float = 0.0) -> None:
        """Log AI model usage.

        Args:
            provider: Provider name.
            model: Model name.
            tokens: Number of tokens used.
            cost: Cost in USD (default: 0.0 for free models).
        """
        cost_str = f"${cost:.4f}" if cost > 0 else "FREE"
        self.logger.info(f"Model usage: {provider}/{model} - {tokens} tokens - {cost_str}")

    def log_error(self, error: Exception, context: Optional[str] = None) -> None:
        """Log an error with context.

        Args:
            error: Exception that occurred.
            context: Optional context information.
        """
        context_str = f" - Context: {context}" if context else ""
        self.logger.error(f"Error: {error}{context_str}", exc_info=True)

    def get_session_log_path(self) -> Optional[Path]:
        """Get the path to the current session log file.

        Returns:
            Path to session log file, or None if no session.
        """
        if not self.session_id:
            return None
        return self.LOG_DIR / f"{self.SESSION_LOG_PREFIX}{self.session_id}.log"

    def cleanup_old_logs(self, days: int = 30) -> None:
        """Clean up log files older than specified days.

        Args:
            days: Number of days to keep logs (default: 30).
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0

        for log_file in self.LOG_DIR.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to delete old log file {log_file}: {e}")

        if deleted_count > 0:
            self.logger.info(f"Cleaned up {deleted_count} old log file(s)")

    def __enter__(self) -> "LoggerManager":
        """Context manager entry.

        Returns:
            Self for use in 'with' statement.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit.

        Args:
            exc_type: Exception type if any.
            exc_val: Exception value if any.
            exc_tb: Exception traceback if any.
        """
        # Clean up handlers if needed
        # For now, we keep handlers active for the session
        pass


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance (convenience function).

    Args:
        name: Optional logger name.

    Returns:
        Logger instance.
    """
    return logging.getLogger(f"omnidev.{name}" if name else "omnidev")

