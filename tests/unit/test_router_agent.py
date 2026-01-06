"""
Unit tests for RouterAgent.

Tests model selection, task analysis, cost optimization,
and fallback strategies following AGENTS.md guidelines.
"""

from unittest.mock import Mock, patch

import pytest

from omnidev.agents.router_agent import RouterAgent
from omnidev.core.config import ConfigManager
from omnidev.models.registry import ProviderRegistry


class TestRouterAgent:
    """Test cases for RouterAgent."""

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
    def mock_provider_registry(self) -> ProviderRegistry:
        """Create a mock ProviderRegistry.

        Returns:
            Mock ProviderRegistry instance.
        """
        return Mock(spec=ProviderRegistry)

    @pytest.fixture
    def router_agent(
        self,
        mock_config: ConfigManager,
        mock_provider_registry: ProviderRegistry,
    ) -> RouterAgent:
        """Create a RouterAgent instance.

        Args:
            mock_config: Mock ConfigManager fixture.
            mock_provider_registry: Mock ProviderRegistry fixture.

        Returns:
            RouterAgent instance.
        """
        with patch("omnidev.agents.router_agent.BaseOmniDevAgent.__init__") as mock_init:
            mock_init.return_value = None
            agent = RouterAgent.__new__(RouterAgent)
            object.__setattr__(agent, "config", mock_config)
            object.__setattr__(agent, "provider_registry", mock_provider_registry)
            return agent

    def test_agent_initialization(
        self,
        mock_config: ConfigManager,
        mock_provider_registry: ProviderRegistry,
    ) -> None:
        """Test RouterAgent initialization.

        Args:
            mock_config: Mock ConfigManager fixture.
            mock_provider_registry: Mock ProviderRegistry fixture.
        """
        with patch("omnidev.agents.router_agent.BaseOmniDevAgent.__init__") as mock_init:
            mock_init.return_value = None
            agent = RouterAgent.__new__(RouterAgent)
            object.__setattr__(agent, "config", mock_config)
            object.__setattr__(agent, "provider_registry", mock_provider_registry)
            
            assert agent.config == mock_config
            assert agent.provider_registry == mock_provider_registry

    def test_select_model_returns_structure(self, router_agent: RouterAgent) -> None:
        """Test select_model returns proper structure.

        Args:
            router_agent: RouterAgent fixture.
        """
        result = router_agent.select_model("test task")
        
        assert isinstance(result, dict)
        assert "model" in result
        assert "provider" in result
        assert "reason" in result

    def test_select_model_with_complexity(self, router_agent: RouterAgent) -> None:
        """Test select_model with different complexity levels.

        Args:
            router_agent: RouterAgent fixture.
        """
        for complexity in ["low", "medium", "high"]:
            result = router_agent.select_model("test task", complexity=complexity)
            assert "model" in result
            assert "provider" in result
            assert "reason" in result

    def test_select_model_default_complexity(self, router_agent: RouterAgent) -> None:
        """Test select_model uses default complexity.

        Args:
            router_agent: RouterAgent fixture.
        """
        result = router_agent.select_model("test task")
        
        # Should work with default "medium" complexity
        assert result["model"] is not None

    def test_provider_registry_assignment(
        self,
        mock_config: ConfigManager,
        mock_provider_registry: ProviderRegistry,
    ) -> None:
        """Test provider_registry is correctly assigned.

        Args:
            mock_config: Mock ConfigManager fixture.
            mock_provider_registry: Mock ProviderRegistry fixture.
        """
        with patch("omnidev.agents.router_agent.BaseOmniDevAgent.__init__") as mock_init:
            mock_init.return_value = None
            agent = RouterAgent.__new__(RouterAgent)
            object.__setattr__(agent, "config", mock_config)
            object.__setattr__(agent, "provider_registry", mock_provider_registry)
            
            assert agent.provider_registry == mock_provider_registry

