"""
Unit tests for BaseOmniDevAgent.

Tests agent initialization, prompt loading, OpenRouter integration,
and error handling following AGENTS.md guidelines.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from omnidev.agents.base import BaseOmniDevAgent
from omnidev.core.config import ConfigManager
from omnidev.core.exceptions import ConfigurationError


class TestBaseOmniDevAgent:
    """Test cases for BaseOmniDevAgent."""

    @pytest.fixture
    def mock_config(self) -> ConfigManager:
        """Create a mock ConfigManager with OpenRouter API key.

        Returns:
            Mock ConfigManager instance.
        """
        config = Mock(spec=ConfigManager)
        config.get_api_key = Mock(return_value="test-api-key")
        
        # Mock model config
        model_config = Mock()
        model_config.agent_model = "mistralai/mistral-7b-instruct"
        project_config = Mock()
        project_config.models = model_config
        config.get_config = Mock(return_value=project_config)
        
        return config

    def test_agent_initialization_success(self, mock_config: ConfigManager) -> None:
        """Test successful agent initialization.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        with patch("omnidev.agents.base.ChatOpenAI") as mock_chat, \
             patch("omnidev.agents.base.Agent.__init__") as mock_agent_init:
            mock_chat.return_value = Mock()
            mock_agent_init.return_value = None
            
            agent = BaseOmniDevAgent(
                role="Test Agent",
                goal="Test goal",
                backstory="Test backstory",
                config=mock_config,
            )
            
            assert agent.config == mock_config
            assert agent.agent_model == "mistralai/mistral-7b-instruct"
            mock_agent_init.assert_called_once()

    def test_agent_initialization_without_api_key(self, mock_config: ConfigManager) -> None:
        """Test agent initialization fails without API key.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        mock_config.get_api_key = Mock(return_value=None)
        
        with pytest.raises(ValueError, match="OpenRouter API key not configured"):
            BaseOmniDevAgent(
                role="Test Agent",
                goal="Test goal",
                backstory="Test backstory",
                config=mock_config,
            )

    def test_agent_initialization_with_custom_model(self, mock_config: ConfigManager) -> None:
        """Test agent initialization with custom model override.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        with patch("omnidev.agents.base.ChatOpenAI") as mock_chat, \
             patch("omnidev.agents.base.Agent.__init__") as mock_agent_init:
            mock_chat.return_value = Mock()
            mock_agent_init.return_value = None
            
            agent = BaseOmniDevAgent(
                role="Test Agent",
                goal="Test goal",
                backstory="Test backstory",
                config=mock_config,
                model="custom-model",
            )
            
            assert agent.agent_model == "custom-model"

    def test_agent_initialization_with_prompt(self, mock_config: ConfigManager) -> None:
        """Test agent initialization with prompt loading.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        with patch("omnidev.agents.base.ChatOpenAI") as mock_chat, \
             patch("omnidev.agents.base.Agent.__init__") as mock_agent_init, \
             patch("omnidev.agents.base.PromptLoader") as mock_loader_class:
            
            mock_chat.return_value = Mock()
            mock_agent_init.return_value = None
            mock_loader = Mock()
            mock_loader.load = Mock(side_effect=["Base prompt", "Agent prompt"])
            mock_loader_class.return_value = mock_loader
            
            agent = BaseOmniDevAgent(
                role="Test Agent",
                goal="Test goal",
                backstory="Test backstory",
                config=mock_config,
                prompt_name="test_agent",
            )
            
            assert agent.system_prompt is not None
            assert "Base prompt" in agent.system_prompt
            assert "Agent prompt" in agent.system_prompt
            mock_loader.load.assert_any_call("agents", "base_agent")
            mock_loader.load.assert_any_call("agents", "test_agent")

    def test_agent_initialization_prompt_load_failure(self, mock_config: ConfigManager) -> None:
        """Test agent initialization handles prompt load failure gracefully.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        with patch("omnidev.agents.base.ChatOpenAI") as mock_chat, \
             patch("omnidev.agents.base.Agent.__init__") as mock_agent_init, \
             patch("omnidev.agents.base.PromptLoader") as mock_loader_class:
            
            mock_chat.return_value = Mock()
            mock_agent_init.return_value = None
            mock_loader = Mock()
            mock_loader.load = Mock(side_effect=ConfigurationError("Prompt not found"))
            mock_loader_class.return_value = mock_loader
            
            # Should not raise, but log warning
            import logging
            logger_name = "omnidev.agents.base"
            with patch.object(logging.getLogger(logger_name), "warning") as mock_warning:
                agent = BaseOmniDevAgent(
                    role="Test Agent",
                    goal="Test goal",
                    backstory="Test backstory",
                    config=mock_config,
                    prompt_name="nonexistent",
                )
                
                assert agent.system_prompt is None
                mock_warning.assert_called_once()

    def test_agent_llm_configuration(self, mock_config: ConfigManager) -> None:
        """Test LLM is configured correctly with OpenRouter.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        with patch("omnidev.agents.base.ChatOpenAI") as mock_chat, \
             patch("omnidev.agents.base.Agent.__init__") as mock_agent_init:
            mock_chat.return_value = Mock()
            mock_agent_init.return_value = None
            
            BaseOmniDevAgent(
                role="Test Agent",
                goal="Test goal",
                backstory="Test backstory",
                config=mock_config,
            )
            
            mock_chat.assert_called_once()
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs["model"] == "mistralai/mistral-7b-instruct"
            assert call_kwargs["openai_api_key"] == "test-api-key"
            assert call_kwargs["base_url"] == "https://openrouter.ai/api/v1"
            assert "HTTP-Referer" in call_kwargs["default_headers"]
            assert "X-Title" in call_kwargs["default_headers"]

    def test_agent_backstory_enhancement_with_prompt(self, mock_config: ConfigManager) -> None:
        """Test backstory is enhanced with system prompt when available.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        with patch("omnidev.agents.base.ChatOpenAI") as mock_chat, \
             patch("omnidev.agents.base.Agent.__init__") as mock_agent_init, \
             patch("omnidev.agents.base.PromptLoader") as mock_loader_class:
            
            mock_chat.return_value = Mock()
            mock_agent_init.return_value = None
            mock_loader = Mock()
            mock_loader.load = Mock(side_effect=["Base prompt", "Agent prompt"])
            mock_loader_class.return_value = mock_loader
            
            BaseOmniDevAgent(
                role="Test Agent",
                goal="Test goal",
                backstory="Original backstory",
                config=mock_config,
                prompt_name="test_agent",
            )
            
            # Verify backstory was enhanced
            call_kwargs = mock_agent_init.call_args[1]
            assert "Original backstory" in call_kwargs["backstory"]
            assert "System Guidelines" in call_kwargs["backstory"]

    def test_agent_crewai_inheritance(self, mock_config: ConfigManager) -> None:
        """Test agent properly inherits from CrewAI Agent.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        with patch("omnidev.agents.base.ChatOpenAI") as mock_chat, \
             patch("omnidev.agents.base.Agent.__init__") as mock_agent_init:
            mock_chat.return_value = Mock()
            mock_agent_init.return_value = None
            
            agent = BaseOmniDevAgent(
                role="Test Agent",
                goal="Test goal",
                backstory="Test backstory",
                config=mock_config,
            )
            
            # Verify it's an instance of Agent (inheritance)
            from crewai import Agent
            assert isinstance(agent, Agent)
            # Verify config is set
            assert agent.config == mock_config

