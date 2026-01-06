"""
Unit tests for prompt system.
"""

import tempfile
from pathlib import Path

import pytest

from omnidev.core.exceptions import ConfigurationError
from omnidev.prompts.loader import PromptLoader
from omnidev.prompts.llm_helper import (
    get_code_generation_prompt,
    get_system_prompt_for_task,
)


class TestPromptLoader:
    """Test PromptLoader functionality."""

    def test_load_prompt(self) -> None:
        """Test loading a prompt file."""
        loader = PromptLoader()
        
        # Load base agent prompt
        prompt = loader.load("agents", "base_agent")
        
        assert prompt is not None
        assert len(prompt) > 0
        assert "OmniDev" in prompt

    def test_load_nonexistent_prompt(self) -> None:
        """Test loading non-existent prompt raises error."""
        loader = PromptLoader()
        
        with pytest.raises(ConfigurationError, match="not found"):
            loader.load("agents", "nonexistent")

    def test_template_substitution(self) -> None:
        """Test template variable substitution."""
        # Create temporary prompt file
        with tempfile.TemporaryDirectory() as tmpdir:
            prompts_dir = Path(tmpdir)
            agents_dir = prompts_dir / "agents"
            agents_dir.mkdir()
            
            # Create test prompt with template
            test_prompt = agents_dir / "test.txt"
            test_prompt.write_text("Hello {name}, you are {role}.")
            
            loader = PromptLoader(prompts_dir)
            result = loader.load("agents", "test", name="Alice", role="developer")
            
            assert result == "Hello Alice, you are developer."

    def test_cache(self) -> None:
        """Test prompt caching."""
        loader = PromptLoader()
        
        # Load same prompt twice
        prompt1 = loader.load("agents", "base_agent")
        prompt2 = loader.load("agents", "base_agent")
        
        # Should be same object (cached)
        assert prompt1 == prompt2

    def test_clear_cache(self) -> None:
        """Test clearing prompt cache."""
        loader = PromptLoader()
        
        # Load and cache
        loader.load("agents", "base_agent")
        assert len(loader._cache) > 0
        
        # Clear cache
        loader.clear_cache()
        assert len(loader._cache) == 0

    def test_get_available_prompts(self) -> None:
        """Test getting list of available prompts."""
        loader = PromptLoader()
        
        prompts = loader.get_available_prompts()
        
        assert len(prompts) > 0
        assert "agents/base_agent" in prompts
        assert "llm/code_generation" in prompts


class TestLLMHelper:
    """Test LLM helper functions."""

    def test_get_code_generation_prompt(self) -> None:
        """Test getting code generation prompt."""
        prompt = get_code_generation_prompt()
        
        assert prompt is not None
        assert len(prompt) > 0
        assert "Code Generation" in prompt or "code generation" in prompt.lower()

    def test_get_system_prompt_for_task(self) -> None:
        """Test getting system prompt for task type."""
        # Test code generation
        prompt = get_system_prompt_for_task("code_gen")
        assert prompt is not None
        assert len(prompt) > 0
        
        # Test code review
        prompt = get_system_prompt_for_task("review")
        assert prompt is not None
        
        # Test unknown task (should default to code generation)
        prompt = get_system_prompt_for_task("unknown")
        assert prompt is not None

