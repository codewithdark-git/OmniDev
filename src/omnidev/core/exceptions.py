"""
Base exception classes for OmniDev.

This module defines the exception hierarchy for OmniDev, providing
specific exception types for different error conditions.
"""


class OmniDevError(Exception):
    """Base exception for all OmniDev errors."""

    def __init__(self, message: str) -> None:
        """Initialize the exception with a message.

        Args:
            message: Error message describing what went wrong.
        """
        self.message = message
        super().__init__(self.message)


class ConfigurationError(OmniDevError):
    """Raised when there's an error with configuration."""

    pass


class ProviderError(OmniDevError):
    """Raised when there's an error with an AI provider."""

    pass


class FileOperationError(OmniDevError):
    """Raised when a file operation fails."""

    pass


class ValidationError(OmniDevError):
    """Raised when validation fails."""

    pass


class ContextError(OmniDevError):
    """Raised when there's an error with context management."""

    pass

