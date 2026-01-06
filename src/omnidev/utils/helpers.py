"""
Helper utilities for OmniDev.

Provides common utility functions used throughout the codebase.
"""

from pathlib import Path
from typing import Optional


def find_project_root(start_path: Optional[Path] = None) -> Path:
    """Find the project root directory.

    Looks for common project markers like .git, .omnidev.yaml, pyproject.toml, etc.

    Args:
        start_path: Starting directory. If None, uses current directory.

    Returns:
        Project root directory.
    """
    if start_path is None:
        start_path = Path.cwd()

    current = Path(start_path).resolve()

    # Markers that indicate project root
    markers = [".git", ".omnidev.yaml", "pyproject.toml", "package.json", "requirements.txt"]

    # Walk up the directory tree
    for path in [current] + list(current.parents):
        for marker in markers:
            if (path / marker).exists():
                return path

    # If no marker found, return the starting directory
    return current


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to be safe for filesystem.

    Args:
        filename: Original filename.

    Returns:
        Sanitized filename.
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, "_")

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")

    # Ensure not empty
    if not sanitized:
        sanitized = "untitled"

    return sanitized


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Formatted size string.
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate.
        max_length: Maximum length.
        suffix: Suffix to add if truncated.

    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix

