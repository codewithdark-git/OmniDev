"""
Configuration management for OmniDev.

This module provides configuration management with support for:
- Global and project-level YAML configuration files
- Secure API key storage using keyring
- Environment variable support
- Project-specific .env file support
- Configuration validation
"""

import os
from pathlib import Path
from typing import Any, Optional

import keyring
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

from omnidev.core.exceptions import ConfigurationError


class ModelConfig(BaseModel):
    """Configuration for AI model preferences."""

    default: str = Field(default="auto", description="Default model to use")
    preferred: Optional[str] = Field(default=None, description="Preferred model for this project")
    fallback: str = Field(default="gpt4free", description="Fallback model provider")
    agent_model: str = Field(
        default="deepseek/deepseek-r1",
        description="Model for agent internal operations (OpenRouter)"
    )
    g4f_providers: list[str] = Field(
        default_factory=lambda: ["PollinationsAI", "Chatai", "ItalyGPT", "FenayAI", "EasyChat", "WeWordle", "DeepInfra"],
        description="GPT4Free providers to use in order of priority"
    )

    @field_validator("default", "preferred", "fallback")
    @classmethod
    def validate_model_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate model name is not empty if provided."""
        if v is not None and not v.strip():
            raise ValueError("Model name cannot be empty")
        return v.strip() if v else v
    
    @field_validator("g4f_providers")
    @classmethod
    def validate_g4f_providers(cls, v: list[str]) -> list[str]:
        """Validate that G4F providers list is not empty."""
        return [p.strip() for p in v if p.strip()] if v else ["PollinationsAI", "Chatai", "ItalyGPT"]


class ContextConfig(BaseModel):
    """Configuration for context management."""

    max_files: int = Field(default=50, ge=1, le=500, description="Maximum files to include")
    max_tokens: int = Field(default=120000, ge=1000, le=1000000, description="Maximum tokens in context")
    auto_prune: bool = Field(default=True, description="Automatically prune context when needed")
    always_include: list[str] = Field(default_factory=list, description="Files to always include")
    exclude: list[str] = Field(default_factory=list, description="Patterns to exclude")

    @field_validator("always_include", "exclude")
    @classmethod
    def validate_patterns(cls, v: list[str]) -> list[str]:
        """Validate that patterns are not empty strings."""
        return [p.strip() for p in v if p.strip()]


class BudgetConfig(BaseModel):
    """Configuration for cost management."""

    daily_limit: float = Field(default=5.0, ge=0.0, description="Daily spending limit in USD")
    warn_at: float = Field(default=4.0, ge=0.0, description="Warn when reaching this amount")
    free_models_first: bool = Field(default=True, description="Prefer free models when possible")

    @field_validator("warn_at")
    @classmethod
    def validate_warn_at(cls, v: float, info: Any) -> float:
        """Ensure warn_at is less than daily_limit."""
        if "daily_limit" in info.data and v >= info.data["daily_limit"]:
            raise ValueError("warn_at must be less than daily_limit")
        return v


class ModeConfig(BaseModel):
    """Configuration for operational modes."""

    default_mode: str = Field(default="agent", description="Default operational mode")
    auto_confirm_file_creation: bool = Field(default=True, description="Auto-confirm file creation")
    auto_confirm_file_editing: bool = Field(default=True, description="Auto-confirm file editing")
    auto_confirm_file_deletion: bool = Field(default=False, description="Auto-confirm file deletion")
    auto_confirm_git_operations: bool = Field(default=True, description="Auto-confirm git operations")


class PromptConfig(BaseModel):
    """Configuration for prompt system."""

    custom_prompts_dir: Optional[str] = Field(default=None, description="Custom prompts directory path")
    prompt_version: str = Field(default="1.0", description="Prompt version for caching")
    enable_prompts: bool = Field(default=True, description="Enable system prompts")


class ProjectConfig(BaseModel):
    """Complete project configuration."""

    project_name: Optional[str] = Field(default=None, description="Project name")
    models: ModelConfig = Field(default_factory=ModelConfig, description="Model configuration")
    context: ContextConfig = Field(default_factory=ContextConfig, description="Context configuration")
    budget: BudgetConfig = Field(default_factory=BudgetConfig, description="Budget configuration")
    prompts: PromptConfig = Field(default_factory=PromptConfig, description="Prompt configuration")
    mode: ModeConfig = Field(default_factory=ModeConfig, description="Mode configuration")


class ConfigManager:
    """Manages configuration for OmniDev.

    Handles loading and merging of global and project-level configurations,
    secure API key storage, and environment variable support.
    """

    SERVICE_NAME = "omnidev"
    GLOBAL_CONFIG_DIR = Path.home() / ".omnidev"
    GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.yaml"
    PROJECT_CONFIG_FILE = Path(".omnidev.yaml")
    PROJECT_ENV_FILE = Path(".env")

    def __init__(self, project_root: Optional[Path] = None) -> None:
        """Initialize the configuration manager.

        Args:
            project_root: Root directory of the project. If None, uses current directory.

        Raises:
            ConfigurationError: If configuration files are invalid.
        """
        self.project_root = project_root or Path.cwd()
        self._global_config: Optional[ProjectConfig] = None
        self._project_config: Optional[ProjectConfig] = None
        self._merged_config: Optional[ProjectConfig] = None
        
        # Load .env file from project root if it exists
        self._load_env_file()

    def load(self) -> ProjectConfig:
        """Load and merge global and project configurations.

        Returns:
            Merged configuration with project config taking precedence.

        Raises:
            ConfigurationError: If configuration loading fails.
        """
        try:
            self._global_config = self._load_global_config()
            self._project_config = self._load_project_config()
            self._merged_config = self._merge_configs()
            return self._merged_config
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    def get_config(self) -> ProjectConfig:
        """Get the current merged configuration.

        Returns:
            Current configuration. Loads if not already loaded.

        Raises:
            ConfigurationError: If configuration is not available.
        """
        if self._merged_config is None:
            return self.load()
        return self._merged_config

    def _load_global_config(self) -> ProjectConfig:
        """Load global configuration from user's home directory.

        Returns:
            Global configuration. Returns defaults if file doesn't exist or is invalid.
        """
        if not self.GLOBAL_CONFIG_FILE.exists():
            return ProjectConfig()

        try:
            with open(self.GLOBAL_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return ProjectConfig(**data)
        except (yaml.YAMLError, Exception):
            # If config file is invalid, return defaults and optionally backup the bad file
            # Don't raise error - just use defaults
            return ProjectConfig()

    def _load_project_config(self) -> Optional[ProjectConfig]:
        """Load project-level configuration from project root.

        Returns:
            Project configuration if file exists, None otherwise.

        Raises:
            ConfigurationError: If project config file is invalid.
        """
        project_config_path = self.project_root / self.PROJECT_CONFIG_FILE
        if not project_config_path.exists():
            return None

        try:
            with open(project_config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return ProjectConfig(**data)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in project config: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load project config: {e}") from e

    def _merge_configs(self) -> ProjectConfig:
        """Merge global and project configurations.

        Project configuration takes precedence over global configuration.

        Returns:
            Merged configuration.
        """
        global_data = self._global_config.model_dump(exclude_none=True)
        project_data = self._project_config.model_dump(exclude_none=True) if self._project_config else {}

        # Deep merge nested configurations
        merged_data = self._deep_merge(global_data, project_data)
        return ProjectConfig(**merged_data)

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary.
            override: Override dictionary (takes precedence).

        Returns:
            Merged dictionary.
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def save_global_config(self, config: ProjectConfig) -> None:
        """Save configuration to global config file.

        Args:
            config: Configuration to save.

        Raises:
            ConfigurationError: If saving fails.
        """
        try:
            self.GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.GLOBAL_CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.dump(config.model_dump(exclude_none=True), f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise ConfigurationError(f"Failed to save global config: {e}") from e

    def save_project_config(self, config: Optional[ProjectConfig] = None) -> None:
        """Save configuration to project config file.

        Args:
            config: Configuration to save. If None, uses current merged configuration.

        Raises:
            ConfigurationError: If saving fails.
        """
        try:
            # Use provided config or current merged config
            config_to_save = config or self.get_config()
            
            project_config_path = self.project_root / self.PROJECT_CONFIG_FILE
            with open(project_config_path, "w", encoding="utf-8") as f:
                yaml.dump(config_to_save.model_dump(exclude_none=True), f, default_flow_style=False, sort_keys=False)
            
            # Update internal project config reference
            self._project_config = config_to_save
            # Re-merge to update merged config
            self._merged_config = self._merge_configs()
        except Exception as e:
            raise ConfigurationError(f"Failed to save project config: {e}") from e

    def _load_env_file(self) -> None:
        """Load .env file from project root if it exists."""
        env_file = self.project_root / self.PROJECT_ENV_FILE
        if env_file.exists():
            load_dotenv(env_file, override=False)

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider from secure storage or environment.

        Checks in this order:
        1. Environment variables (OMNIDEV_{PROVIDER}_API_KEY)
        2. Project .env file (OMNIDEV_{PROVIDER}_API_KEY)
        3. Keyring secure storage

        Args:
            provider: Provider name (e.g., 'openrouter', 'openai', 'anthropic').

        Returns:
            API key if found, None otherwise.
        """
        # First check environment variables (already loaded from .env if exists)
        env_key = f"OMNIDEV_{provider.upper()}_API_KEY"
        env_value = os.getenv(env_key)
        if env_value:
            return env_value
        
        # Also check provider-specific env var (for backward compatibility)
        provider_env_key = f"{provider.upper()}_API_KEY"
        provider_env_value = os.getenv(provider_env_key)
        if provider_env_value:
            return provider_env_value

        # Then check keyring
        try:
            keyring_value = keyring.get_password(self.SERVICE_NAME, provider)
            if keyring_value:
                return keyring_value
        except Exception:
            # Keyring might not be available, ignore
            pass

        return None

    def set_api_key(self, provider: str, api_key: str) -> None:
        """Store API key securely using keyring.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic').
            api_key: API key to store.

        Raises:
            ConfigurationError: If storing the key fails.
        """
        if not api_key or not api_key.strip():
            raise ConfigurationError("API key cannot be empty")

        try:
            keyring.set_password(self.SERVICE_NAME, provider, api_key.strip())
        except Exception as e:
            raise ConfigurationError(f"Failed to store API key: {e}") from e

    def delete_api_key(self, provider: str) -> None:
        """Delete API key from secure storage.

        Args:
            provider: Provider name to delete key for.

        Raises:
            ConfigurationError: If deletion fails.
        """
        try:
            keyring.delete_password(self.SERVICE_NAME, provider)
        except keyring.errors.PasswordDeleteError:
            # Key doesn't exist, that's fine
            pass
        except Exception as e:
            raise ConfigurationError(f"Failed to delete API key: {e}") from e

    def set_api_key_to_env(self, provider: str, api_key: str) -> None:
        """Store API key in project .env file.

        Args:
            provider: Provider name (e.g., 'openrouter', 'openai').
            api_key: API key to store.

        Raises:
            ConfigurationError: If storing the key fails.
        """
        if not api_key or not api_key.strip():
            raise ConfigurationError("API key cannot be empty")

        env_file = self.project_root / self.PROJECT_ENV_FILE
        env_key = f"OMNIDEV_{provider.upper()}_API_KEY"
        
        # Read existing .env file if it exists
        env_vars: dict[str, str] = {}
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
        
        # Update or add the API key
        env_vars[env_key] = api_key.strip()
        
        # Write back to .env file
        try:
            with open(env_file, "w", encoding="utf-8") as f:
                f.write("# OmniDev API Keys\n")
                f.write("# This file is managed by OmniDev. Do not commit to version control.\n\n")
                for key, value in sorted(env_vars.items()):
                    f.write(f"{key}={value}\n")
            
            # Reload .env file to make it available immediately
            load_dotenv(env_file, override=True)
        except Exception as e:
            raise ConfigurationError(f"Failed to save API key to .env file: {e}") from e

    def list_api_keys(self) -> list[str]:
        """List all providers with stored API keys.

        Returns:
            List of provider names that have API keys stored.
        """
        providers = ["openrouter", "openai", "anthropic", "google", "deepseek"]
        stored_keys = []
        for provider in providers:
            if self.get_api_key(provider) is not None:
                stored_keys.append(provider)
        return stored_keys

