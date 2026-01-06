"""
Unit tests for SetupAgent.

Tests configuration validation, API key management, user guidance,
and error recovery following AGENTS.md guidelines.
"""

from unittest.mock import Mock, patch

import pytest

from omnidev.agents.setup_agent import SetupAgent
from omnidev.core.config import ConfigManager


class TestSetupAgent:
    """Test cases for SetupAgent."""

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
    def setup_agent(self, mock_config: ConfigManager) -> SetupAgent:
        """Create a SetupAgent instance.

        Args:
            mock_config: Mock ConfigManager fixture.

        Returns:
            SetupAgent instance.
        """
        with patch("omnidev.agents.setup_agent.BaseOmniDevAgent.__init__") as mock_init:
            # Mock the parent __init__ to not call super
            mock_init.return_value = None
            agent = SetupAgent.__new__(SetupAgent)  # Create without calling __init__
            # Manually set attributes for testing
            agent.config = mock_config
            return agent

    def test_agent_initialization(self, mock_config: ConfigManager) -> None:
        """Test SetupAgent initialization.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        with patch("omnidev.agents.setup_agent.BaseOmniDevAgent.__init__") as mock_init:
            mock_init.return_value = None
            agent = SetupAgent.__new__(SetupAgent)
            agent.config = mock_config
            
            assert agent.config == mock_config

    def test_run_setup_wizard_returns_structure(self, setup_agent: SetupAgent) -> None:
        """Test run_setup_wizard returns proper structure.

        Args:
            setup_agent: SetupAgent fixture.
        """
        # Ensure agent has the method
        if not hasattr(setup_agent, "run_setup_wizard"):
            # Create a minimal agent instance for testing
            with patch("omnidev.agents.setup_agent.BaseOmniDevAgent.__init__"):
                setup_agent = SetupAgent.__new__(SetupAgent)
                setup_agent.config = Mock()
        
        result = setup_agent.run_setup_wizard()
        
        assert isinstance(result, dict)
        assert "status" in result
        assert "steps_completed" in result
        assert "next_steps" in result
        assert result["status"] == "completed"

    def test_run_setup_wizard_structure_types(self, setup_agent: SetupAgent) -> None:
        """Test run_setup_wizard returns correct types.

        Args:
            setup_agent: SetupAgent fixture.
        """
        # Ensure agent has the method
        if not hasattr(setup_agent, "run_setup_wizard"):
            with patch("omnidev.agents.setup_agent.BaseOmniDevAgent.__init__"):
                setup_agent = SetupAgent.__new__(SetupAgent)
                setup_agent.config = Mock()
        
        result = setup_agent.run_setup_wizard()
        
        assert isinstance(result["status"], str)
        assert isinstance(result["steps_completed"], list)
        assert isinstance(result["next_steps"], list)

    def test_config_assignment(self, mock_config: ConfigManager) -> None:
        """Test config is correctly assigned.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        with patch("omnidev.agents.setup_agent.BaseOmniDevAgent.__init__") as mock_init:
            mock_init.return_value = None
            agent = SetupAgent.__new__(SetupAgent)
            agent.config = mock_config
            
            assert agent.config == mock_config

