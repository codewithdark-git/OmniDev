"""Unit tests for configuration management."""

import tempfile
from pathlib import Path

import pytest
import yaml

from omnidev.core.config import ConfigManager, ConfigurationError, ProjectConfig
from omnidev.core.exceptions import ConfigurationError as ConfigError


class TestConfigManager:
    """Test cases for ConfigManager."""

    def test_config_manager_initialization(self) -> None:
        """Test ConfigManager initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = ConfigManager(project_root)
            # Compare resolved paths (handles Windows short path differences)
            assert config.project_root.resolve() == project_root.resolve()

    def test_load_default_config(self) -> None:
        """Test loading default configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = ConfigManager(project_root)
            loaded = config.load()
            assert isinstance(loaded, ProjectConfig)

    def test_save_and_load_global_config(self) -> None:
        """Test saving and loading global configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = ConfigManager(project_root)
            project_config = ProjectConfig()
            project_config.models.default = "gpt-4o"

            config.save_global_config(project_config)
            loaded = config.load()

            assert loaded.models.default == "gpt-4o"

    def test_project_config_override(self) -> None:
        """Test that project config overrides global config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = ConfigManager(project_root)

            # Set global config
            global_config = ProjectConfig()
            global_config.models.default = "gpt-4o"
            config.save_global_config(global_config)

            # Set project config
            project_config = ProjectConfig()
            project_config.models.default = "claude-sonnet-4"
            config.save_project_config(project_config)

            # Load and verify override
            loaded = config.load()
            assert loaded.models.default == "claude-sonnet-4"

    def test_api_key_storage(self) -> None:
        """Test API key storage and retrieval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = ConfigManager(project_root)

            # Set API key
            config.set_api_key("openai", "test-key-123")

            # Retrieve API key
            retrieved = config.get_api_key("openai")
            assert retrieved == "test-key-123"

            # Delete API key
            config.delete_api_key("openai")
            assert config.get_api_key("openai") is None

    def test_invalid_config_file(self) -> None:
        """Test handling of invalid config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = ConfigManager(project_root)

            # Create invalid YAML file
            invalid_file = config.GLOBAL_CONFIG_FILE
            invalid_file.parent.mkdir(parents=True, exist_ok=True)
            invalid_file.write_text("invalid: yaml: content: [", encoding="utf-8")

            # Should not raise error, but use defaults instead (graceful degradation)
            config.load()
            # Verify defaults are used
            project_config = config.get_config()
            assert project_config.models.default == "auto"

