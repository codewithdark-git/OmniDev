"""
Integration tests for prompt-agent integration.

Tests prompt loading, template substitution, and system prompt injection,
following AGENTS.md guidelines.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from omnidev.agents.base import BaseOmniDevAgent
from omnidev.agents.file_agent import FileProcessingAgent
from omnidev.core.config import ConfigManager
from omnidev.prompts.loader import PromptLoader


class TestPromptAgentIntegration:
    """Integration tests for prompt-agent integration."""

    @pytest.fixture
    def mock_config(self) -> ConfigManager:
        """Create a mock ConfigManager.

        Returns:
            Mock ConfigManager instance.
        """
        config = Mock(spec=ConfigManager)
        config.get_api_key = Mock(return_value="test-api-key")
        model_config = Mock()
        model_config.agent_model = "mistralai/mistral-7b-instruct"
        project_config = Mock()
        project_config.models = model_config
        config.get_config = Mock(return_value=project_config)
        return config

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        """Create a temporary project root.

        Args:
            tmp_path: Pytest temporary path fixture.

        Returns:
            Temporary project root path.
        """
        return tmp_path

    def test_base_agent_loads_prompts(self, mock_config: ConfigManager) -> None:
        """Test BaseOmniDevAgent loads prompts correctly.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        with patch("omnidev.agents.base.ChatOpenAI"), \
             patch("omnidev.agents.base.PromptLoader") as mock_loader_class:
            
            mock_loader = Mock()
            mock_loader.load = Mock(side_effect=["Base prompt", "File agent prompt"])
            mock_loader_class.return_value = mock_loader
            
            agent = BaseOmniDevAgent(
                role="Test",
                goal="Test goal",
                backstory="Test backstory",
                config=mock_config,
                prompt_name="file_agent",
            )
            
            assert agent.system_prompt is not None
            assert "Base prompt" in agent.system_prompt
            assert "File agent prompt" in agent.system_prompt

    def test_file_agent_uses_prompt_name(self, mock_config: ConfigManager, project_root: Path) -> None:
        """Test FileProcessingAgent uses correct prompt name.

        Args:
            mock_config: Mock ConfigManager fixture.
            project_root: Project root fixture.
        """
        with patch("omnidev.agents.file_agent.BaseOmniDevAgent.__init__") as mock_base_init, \
             patch("omnidev.agents.file_agent.FileOperations"):
            
            FileProcessingAgent(mock_config, project_root)
            
            # Verify prompt_name was passed
            call_kwargs = mock_base_init.call_args[1]
            assert call_kwargs["prompt_name"] == "file_agent"

    def test_prompt_loader_integration(self, mock_config: ConfigManager) -> None:
        """Test PromptLoader integration with agents.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        loader = PromptLoader()
        
        # Verify prompts exist
        prompts = loader.get_available_prompts()
        assert "agents/base_agent" in prompts
        assert "agents/file_agent" in prompts
        assert "templates/agent_mode" in prompts
        assert "templates/planning_mode" in prompts

    def test_agent_prompt_combination(self, mock_config: ConfigManager) -> None:
        """Test base and agent prompts are combined correctly.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        with patch("omnidev.agents.base.ChatOpenAI"), \
             patch("omnidev.agents.base.PromptLoader") as mock_loader_class:
            
            mock_loader = Mock()
            base_prompt = "Base agent prompt content"
            agent_prompt = "File agent specific prompt"
            mock_loader.load = Mock(side_effect=[base_prompt, agent_prompt])
            mock_loader_class.return_value = mock_loader
            
            agent = BaseOmniDevAgent(
                role="Test",
                goal="Test goal",
                backstory="Test backstory",
                config=mock_config,
                prompt_name="file_agent",
            )
            
            # Verify prompts are combined
            assert base_prompt in agent.system_prompt
            assert agent_prompt in agent.system_prompt

    def test_prompt_load_failure_handling(self, mock_config: ConfigManager) -> None:
        """Test agent handles prompt load failures gracefully.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        with patch("omnidev.agents.base.ChatOpenAI"), \
             patch("omnidev.agents.base.PromptLoader") as mock_loader_class, \
             patch("omnidev.agents.base.logging") as mock_logging:
            
            mock_loader = Mock()
            mock_loader.load = Mock(side_effect=Exception("Prompt not found"))
            mock_loader_class.return_value = mock_loader
            
            agent = BaseOmniDevAgent(
                role="Test",
                goal="Test goal",
                backstory="Test backstory",
                config=mock_config,
                prompt_name="nonexistent",
            )
            
            # Should not raise, but log warning
            assert agent.system_prompt is None
            mock_logging.getLogger.return_value.warning.assert_called()

    def test_all_agents_have_prompts(self) -> None:
        """Test all agents have corresponding prompt files.

        This test verifies that prompt files exist for all agents.
        """
        loader = PromptLoader()
        prompts = loader.get_available_prompts()
        
        agent_prompts = [p for p in prompts if p.startswith("agents/")]
        
        # Verify key agent prompts exist
        expected_agents = [
            "base_agent",
            "file_agent",
            "setup_agent",
            "context_agent",
            "router_agent",
            "task_agent",
            "validator_agent",
        ]
        
        for agent_name in expected_agents:
            assert f"agents/{agent_name}" in prompts, f"Missing prompt for {agent_name}"

