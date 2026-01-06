"""
Integration tests for agent workflows.

Tests agent-to-agent communication, agent workflows,
and end-to-end scenarios following AGENTS.md guidelines.
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from omnidev.agents.manager import AgentManager
from omnidev.agents.crews import OmniDevCrews
from omnidev.context.manager import ContextManager
from omnidev.core.config import ConfigManager
from omnidev.models.registry import ProviderRegistry


class TestAgentIntegration:
    """Integration tests for agent workflows."""

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

    @pytest.fixture
    def mock_context_manager(self) -> ContextManager:
        """Create a mock ContextManager.

        Returns:
            Mock ContextManager instance.
        """
        context_manager = Mock(spec=ContextManager)
        context_manager.build_context = Mock(return_value={"files": []})
        return context_manager

    @pytest.fixture
    def mock_provider_registry(self) -> ProviderRegistry:
        """Create a mock ProviderRegistry.

        Returns:
            Mock ProviderRegistry instance.
        """
        return Mock(spec=ProviderRegistry)

    @pytest.fixture
    def agent_manager(self, mock_config: ConfigManager) -> AgentManager:
        """Create an AgentManager instance.

        Args:
            mock_config: Mock ConfigManager fixture.

        Returns:
            AgentManager instance.
        """
        return AgentManager(mock_config)

    def test_agent_manager_with_crews(
        self,
        agent_manager: AgentManager,
        mock_config: ConfigManager,
        project_root: Path,
        mock_context_manager: ContextManager,
        mock_provider_registry: ProviderRegistry,
    ) -> None:
        """Test AgentManager integration with crews.

        Args:
            agent_manager: AgentManager fixture.
            mock_config: Mock ConfigManager fixture.
            project_root: Project root fixture.
            mock_context_manager: Mock ContextManager fixture.
            mock_provider_registry: Mock ProviderRegistry fixture.
        """
        with patch("omnidev.agents.crews.FileProcessingAgent"), \
             patch("omnidev.agents.crews.ContextAgent"), \
             patch("omnidev.agents.crews.RouterAgent"), \
             patch("omnidev.agents.crews.TaskAgent"), \
             patch("omnidev.agents.crews.ValidatorAgent"):
            crews = OmniDevCrews(
                mock_config,
                project_root,
                mock_context_manager,
                mock_provider_registry,
            )
            
            # Register crew
            mock_crew = Mock()
            mock_crew.kickoff = Mock(return_value="result")
            agent_manager.register_crew("test_crew", mock_crew)
            
            # Verify crew is registered
            assert agent_manager.get_crew("test_crew") == mock_crew

    @pytest.mark.asyncio
    async def test_crew_execution_workflow(
        self,
        agent_manager: AgentManager,
    ) -> None:
        """Test complete crew execution workflow.

        Args:
            agent_manager: AgentManager fixture.
        """
        mock_crew = Mock()
        mock_crew.kickoff = AsyncMock(return_value="execution result")
        agent_manager.register_crew("workflow_crew", mock_crew)
        
        result = await agent_manager.execute_crew("workflow_crew", "test task")
        
        assert result == "execution result"
        mock_crew.kickoff.assert_called_once()

    def test_multiple_agents_registration(self, agent_manager: AgentManager) -> None:
        """Test registering multiple agents.

        Args:
            agent_manager: AgentManager fixture.
        """
        agents = {
            "file_agent": Mock(),
            "context_agent": Mock(),
            "router_agent": Mock(),
            "task_agent": Mock(),
            "validator_agent": Mock(),
        }
        
        for name, agent in agents.items():
            agent_manager.register_agent(name, agent)
        
        # Verify all agents are registered
        for name, agent in agents.items():
            assert agent_manager.get_agent(name) == agent

    def test_multiple_crews_registration(self, agent_manager: AgentManager) -> None:
        """Test registering multiple crews.

        Args:
            agent_manager: AgentManager fixture.
        """
        crews = {
            "code_generation": Mock(),
            "file_operations": Mock(),
        }
        
        for name, crew in crews.items():
            agent_manager.register_crew(name, crew)
        
        # Verify all crews are registered
        for name, crew in crews.items():
            assert agent_manager.get_crew(name) == crew

