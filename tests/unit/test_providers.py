"""Unit tests for AI providers."""

import pytest

from omnidev.core.exceptions import ProviderError
from omnidev.models.base import BaseProvider, ProviderResponse
from omnidev.models.providers.gpt4free import GPT4FreeProvider


class TestBaseProvider:
    """Test cases for BaseProvider interface."""

    def test_provider_initialization(self) -> None:
        """Test provider initialization."""
        # This would test a concrete implementation
        pass


class TestGPT4FreeProvider:
    """Test cases for GPT4FreeProvider."""

    def test_provider_initialization_without_g4f(self) -> None:
        """Test provider initialization when g4f is not available."""
        # Mock scenario where g4f is not installed
        import sys
        original_modules = sys.modules.copy()

        # Remove g4f if it exists
        if "g4f" in sys.modules:
            del sys.modules["g4f"]

        # This test would verify error handling
        # In actual implementation, we'd use mocking
        pass

    def test_list_models(self) -> None:
        """Test listing available models."""
        try:
            provider = GPT4FreeProvider()
            models = provider.list_models()
            assert isinstance(models, list)
            assert len(models) > 0
        except ProviderError:
            # g4f might not be available in test environment
            pytest.skip("g4f not available")

    def test_is_model_available(self) -> None:
        """Test model availability check."""
        try:
            provider = GPT4FreeProvider()
            assert provider.is_model_available("gpt-4o")
            assert not provider.is_model_available("non-existent-model")
        except ProviderError:
            pytest.skip("g4f not available")

