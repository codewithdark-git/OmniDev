"""
Prompt loader and management system.

Handles loading, caching, and template substitution for system prompts.
"""

import os
from pathlib import Path
from typing import Any, Optional

from omnidev.core.exceptions import ConfigurationError


class PromptLoader:
    """Loads and manages system prompts with caching and template support."""

    def __init__(self, prompts_dir: Optional[Path] = None) -> None:
        """Initialize prompt loader.

        Args:
            prompts_dir: Base directory for prompts. Defaults to package prompts directory.
        """
        if prompts_dir is None:
            # Get the prompts directory relative to this file
            current_file = Path(__file__).resolve()
            prompts_dir = current_file.parent
        
        self.prompts_dir = Path(prompts_dir)
        self._cache: dict[str, str] = {}
        
        if not self.prompts_dir.exists():
            raise ConfigurationError(f"Prompts directory not found: {self.prompts_dir}")

    def load(self, category: str, name: str, **kwargs: Any) -> str:
        """Load a prompt file with optional template variables.

        Args:
            category: Prompt category (agents, llm, best_practices, templates).
            name: Prompt name (without .txt extension).
            **kwargs: Template variables to substitute.

        Returns:
            Loaded prompt text with variables substituted.

        Raises:
            ConfigurationError: If prompt file not found.
        """
        cache_key = f"{category}/{name}"
        
        # Check cache first
        if cache_key in self._cache and not kwargs:
            return self._cache[cache_key]
        
        # Load from file
        prompt_path = self.prompts_dir / category / f"{name}.txt"
        
        if not prompt_path.exists():
            raise ConfigurationError(f"Prompt file not found: {prompt_path}")
        
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise ConfigurationError(f"Failed to load prompt {prompt_path}: {e}") from e
        
        # Substitute template variables
        if kwargs:
            content = self._substitute_variables(content, kwargs)
        else:
            # Cache if no variables
            self._cache[cache_key] = content
        
        return content

    def _substitute_variables(self, template: str, variables: dict[str, Any]) -> str:
        """Substitute template variables in prompt text.

        Args:
            template: Template string with {variable} placeholders.
            variables: Dictionary of variable values.

        Returns:
            Template with variables substituted.
        """
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ConfigurationError(f"Missing template variable: {e}") from e

    def clear_cache(self) -> None:
        """Clear the prompt cache."""
        self._cache.clear()

    def get_available_prompts(self, category: Optional[str] = None) -> list[str]:
        """Get list of available prompts.

        Args:
            category: Optional category to filter by.

        Returns:
            List of prompt names (category/name format).
        """
        prompts = []
        
        if category:
            categories = [category]
        else:
            categories = [d.name for d in self.prompts_dir.iterdir() if d.is_dir()]
        
        for cat in categories:
            cat_dir = self.prompts_dir / cat
            if cat_dir.exists():
                for file in cat_dir.glob("*.txt"):
                    prompts.append(f"{cat}/{file.stem}")
        
        return sorted(prompts)

