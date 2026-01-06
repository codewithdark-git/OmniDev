"""
Unit tests for AgentManager.

Tests agent lifecycle, resource pooling, crew orchestration,
and error handling following AGENTS.md guidelines.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from omnidev.agents.manager import AgentManager
from omnidev.core.config import ConfigManager
from omnidev.core.exceptions import OmniDevError


class TestAgentManager:
    """Test cases for AgentManager."""

    @pytest.fixture
    def mock_config(self) -> ConfigManager:
        """Create a mock ConfigManager.

        Returns:
            Mock ConfigManager instance.
        """
        return Mock(spec=ConfigManager)

    @pytest.fixture
    def agent_manager(self, mock_config: ConfigManager) -> AgentManager:
        """Create an AgentManager instance.

        Args:
            mock_config: Mock ConfigManager fixture.

        Returns:
            AgentManager instance.
        """
        return AgentManager(mock_config)

    def test_manager_initialization(self, mock_config: ConfigManager) -> None:
        """Test AgentManager initialization.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        manager = AgentManager(mock_config)
        
        assert manager.config == mock_config
        assert isinstance(manager.agents, dict)
        assert isinstance(manager.crews, dict)

    def test_register_agent(self, agent_manager: AgentManager) -> None:
        """Test registering an agent.

        Args:
            agent_manager: AgentManager fixture.
        """
        mock_agent = Mock()
        agent_manager.register_agent("test_agent", mock_agent)
        
        assert "test_agent" in agent_manager.agents
        assert agent_manager.agents["test_agent"] == mock_agent

    def test_get_agent_existing(self, agent_manager: AgentManager) -> None:
        """Test getting an existing agent.

        Args:
            agent_manager: AgentManager fixture.
        """
        mock_agent = Mock()
        agent_manager.register_agent("test_agent", mock_agent)
        
        result = agent_manager.get_agent("test_agent")
        
        assert result == mock_agent

    def test_get_agent_nonexistent(self, agent_manager: AgentManager) -> None:
        """Test getting a non-existent agent returns None.

        Args:
            agent_manager: AgentManager fixture.
        """
        result = agent_manager.get_agent("nonexistent")
        
        assert result is None

    def test_register_crew(self, agent_manager: AgentManager) -> None:
        """Test registering a crew.

        Args:
            agent_manager: AgentManager fixture.
        """
        mock_crew = Mock()
        agent_manager.register_crew("test_crew", mock_crew)
        
        assert "test_crew" in agent_manager.crews
        assert agent_manager.crews["test_crew"] == mock_crew

    def test_get_crew_existing(self, agent_manager: AgentManager) -> None:
        """Test getting an existing crew.

        Args:
            agent_manager: AgentManager fixture.
        """
        mock_crew = Mock()
        agent_manager.register_crew("test_crew", mock_crew)
        
        result = agent_manager.get_crew("test_crew")
        
        assert result == mock_crew

    def test_get_crew_nonexistent(self, agent_manager: AgentManager) -> None:
        """Test getting a non-existent crew returns None.

        Args:
            agent_manager: AgentManager fixture.
        """
        result = agent_manager.get_crew("nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_crew_success(self, agent_manager: AgentManager) -> None:
        """Test successful crew execution.

        Args:
            agent_manager: AgentManager fixture.
        """
        mock_crew = Mock()
        mock_crew.kickoff = Mock(return_value="execution result")
        agent_manager.register_crew("test_crew", mock_crew)
        
        result = await agent_manager.execute_crew("test_crew", "test task")
        
        assert result == "execution result"
        mock_crew.kickoff.assert_called_once_with(inputs={"task": "test task"})

    @pytest.mark.asyncio
    async def test_execute_crew_not_found(self, agent_manager: AgentManager) -> None:
        """Test execute_crew raises error when crew not found.

        Args:
            agent_manager: AgentManager fixture.
        """
        with pytest.raises(OmniDevError, match="not found"):
            await agent_manager.execute_crew("nonexistent", "test task")

    @pytest.mark.asyncio
    async def test_execute_crew_execution_failure(self, agent_manager: AgentManager) -> None:
        """Test execute_crew handles execution failures.

        Args:
            agent_manager: AgentManager fixture.
        """
        mock_crew = Mock()
        mock_crew.kickoff = Mock(side_effect=Exception("Execution failed"))
        agent_manager.register_crew("test_crew", mock_crew)
        
        with pytest.raises(OmniDevError, match="Crew execution failed"):
            await agent_manager.execute_crew("test_crew", "test task")

    @pytest.mark.asyncio
    async def test_execute_crew_with_kwargs(self, agent_manager: AgentManager) -> None:
        """Test execute_crew passes additional kwargs.

        Args:
            agent_manager: AgentManager fixture.
        """
        mock_crew = Mock()
        mock_crew.kickoff = Mock(return_value="result")
        agent_manager.register_crew("test_crew", mock_crew)
        
        await agent_manager.execute_crew(
            "test_crew",
            "test task",
            param1="value1",
            param2="value2",
        )
        
        # Check call was made with correct inputs
        mock_crew.kickoff.assert_called_once()
        call_kwargs = mock_crew.kickoff.call_args[1]["inputs"]
        assert call_kwargs["task"] == "test task"
        assert call_kwargs["param1"] == "value1"
        assert call_kwargs["param2"] == "value2"

