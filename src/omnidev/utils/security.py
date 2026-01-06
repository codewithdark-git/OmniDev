"""
Security utilities for OmniDev.

Provides security-related functions for safe operations.
"""

from pathlib import Path
from typing import Optional

from omnidev.core.exceptions import ValidationError


def validate_file_path(file_path: Path, project_root: Path) -> Path:
    """Validate that a file path is safe and within project root.

    Args:
        file_path: Path to validate.
        project_root: Project root directory.

    Returns:
        Resolved absolute path.

    Raises:
        ValidationError: If path is invalid or unsafe.
    """
    # Resolve to absolute path
    if file_path.is_absolute():
        resolved = file_path.resolve()
    else:
        resolved = (project_root / file_path).resolve()

    # Check for directory traversal
    try:
        resolved.relative_to(project_root.resolve())
    except ValueError:
        raise ValidationError(f"Path is outside project root: {file_path}")

    # Check for dangerous patterns
    path_str = str(resolved)
    dangerous_patterns = ["..", "~", "/etc", "/sys", "/proc", "C:\\Windows"]
    for pattern in dangerous_patterns:
        if pattern in path_str:
            raise ValidationError(f"Path contains dangerous pattern: {pattern}")

    return resolved


def sanitize_command(command: str) -> str:
    """Sanitize a shell command to prevent injection.

    Args:
        command: Command string to sanitize.

    Returns:
        Sanitized command.

    Raises:
        ValidationError: If command contains dangerous characters.
    """
    dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
    for char in dangerous_chars:
        if char in command:
            raise ValidationError(f"Command contains dangerous character: {char}")

    return command.strip()


def is_safe_to_modify(file_path: Path) -> bool:
    """Check if a file is safe to modify.

    Args:
        file_path: Path to the file.

    Returns:
        True if safe to modify, False otherwise.
    """
    # Check for system files
    system_patterns = [
        "/etc/",
        "/sys/",
        "/proc/",
        "/dev/",
        "C:\\Windows\\",
        "C:\\Program Files\\",
    ]

    path_str = str(file_path.resolve())
    for pattern in system_patterns:
        if pattern in path_str:
            return False

    # Check for hidden system files
    if file_path.name.startswith(".") and file_path.name in [".bashrc", ".profile", ".zshrc"]:
        return False

    return True

