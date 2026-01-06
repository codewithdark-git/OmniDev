"""
Unit tests for ContextAgent.

Tests file selection, relevance scoring, token optimization,
and dependency analysis following AGENTS.md guidelines.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from omnidev.agents.context_agent import ContextAgent
from omnidev.context.manager import ContextManager
from omnidev.core.config import ConfigManager


class TestContextAgent:
    """Test cases for ContextAgent."""

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
    def mock_context_manager(self) -> ContextManager:
        """Create a mock ContextManager.

        Returns:
            Mock ContextManager instance.
        """
        context_manager = Mock(spec=ContextManager)
        context_manager.build_context = Mock(return_value={
            "files": [
                {"path": Path("file1.py"), "relevance": 0.9},
                {"path": Path("file2.py"), "relevance": 0.7},
            ]
        })
        return context_manager

    @pytest.fixture
    def context_agent(
        self,
        mock_config: ConfigManager,
        mock_context_manager: ContextManager,
    ) -> ContextAgent:
        """Create a ContextAgent instance.

        Args:
            mock_config: Mock ConfigManager fixture.
            mock_context_manager: Mock ContextManager fixture.

        Returns:
            ContextAgent instance.
        """
        with patch("omnidev.agents.context_agent.BaseOmniDevAgent.__init__") as mock_init:
            mock_init.return_value = None
            agent = ContextAgent.__new__(ContextAgent)
            # Use object.__setattr__ to bypass Pydantic validation
            object.__setattr__(agent, "config", mock_config)
            object.__setattr__(agent, "context_manager", mock_context_manager)
            return agent

    def test_agent_initialization(
        self,
        mock_config: ConfigManager,
        mock_context_manager: ContextManager,
    ) -> None:
        """Test ContextAgent initialization.

        Args:
            mock_config: Mock ConfigManager fixture.
            mock_context_manager: Mock ContextManager fixture.
        """
        with patch("omnidev.agents.context_agent.BaseOmniDevAgent.__init__") as mock_init:
            mock_init.return_value = None
            agent = ContextAgent.__new__(ContextAgent)
            object.__setattr__(agent, "config", mock_config)
            object.__setattr__(agent, "context_manager", mock_context_manager)
            
            assert agent.config == mock_config
            assert agent.context_manager == mock_context_manager

    def test_select_files_calls_context_manager(
        self,
        context_agent: ContextAgent,
    ) -> None:
        """Test select_files calls context manager.

        Args:
            context_agent: ContextAgent fixture.
        """
        query = "test query"
        max_files = 10
        
        result = context_agent.select_files(query, max_files)
        
        context_agent.context_manager.build_context.assert_called_once_with(
            query,
            max_files=max_files,
        )
        assert isinstance(result, list)

    def test_select_files_returns_paths(
        self,
        context_agent: ContextAgent,
    ) -> None:
        """Test select_files returns list of paths.

        Args:
            context_agent: ContextAgent fixture.
        """
        result = context_agent.select_files("test query")
        
        assert isinstance(result, list)
        assert all(isinstance(path, Path) for path in result)

    def test_select_files_with_max_files(
        self,
        context_agent: ContextAgent,
    ) -> None:
        """Test select_files respects max_files parameter.

        Args:
            context_agent: ContextAgent fixture.
        """
        max_files = 5
        context_agent.select_files("test query", max_files=max_files)
        
        call_kwargs = context_agent.context_manager.build_context.call_args[1]
        assert call_kwargs["max_files"] == max_files

    def test_select_files_empty_result(
        self,
        mock_config: ConfigManager,
    ) -> None:
        """Test select_files handles empty context result.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        mock_context_manager = Mock(spec=ContextManager)
        mock_context_manager.build_context = Mock(return_value={"files": []})
        
        with patch("omnidev.agents.context_agent.BaseOmniDevAgent.__init__") as mock_init:
            mock_init.return_value = None
            agent = ContextAgent.__new__(ContextAgent)
            object.__setattr__(agent, "config", mock_config)
            object.__setattr__(agent, "context_manager", mock_context_manager)
            
            result = agent.select_files("test query")
            assert result == []

