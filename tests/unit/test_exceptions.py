"""Unit tests for exception classes."""

import pytest

from omnidev.core.exceptions import (
    ConfigurationError,
    ContextError,
    FileOperationError,
    OmniDevError,
    ProviderError,
    ValidationError,
)


class TestOmniDevError:
    """Test cases for base OmniDevError."""

    def test_error_message(self) -> None:
        """Test that error message is stored correctly."""
        error = OmniDevError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"


class TestSpecificErrors:
    """Test cases for specific error types."""

    def test_configuration_error(self) -> None:
        """Test ConfigurationError."""
        error = ConfigurationError("Configuration failed")
        assert isinstance(error, OmniDevError)
        assert str(error) == "Configuration failed"

    def test_provider_error(self) -> None:
        """Test ProviderError."""
        error = ProviderError("Provider unavailable")
        assert isinstance(error, OmniDevError)
        assert str(error) == "Provider unavailable"

    def test_file_operation_error(self) -> None:
        """Test FileOperationError."""
        error = FileOperationError("File operation failed")
        assert isinstance(error, OmniDevError)
        assert str(error) == "File operation failed"

    def test_validation_error(self) -> None:
        """Test ValidationError."""
        error = ValidationError("Validation failed")
        assert isinstance(error, OmniDevError)
        assert str(error) == "Validation failed"

    def test_context_error(self) -> None:
        """Test ContextError."""
        error = ContextError("Context error")
        assert isinstance(error, OmniDevError)
        assert str(error) == "Context error"

