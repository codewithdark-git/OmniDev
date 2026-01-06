"""
Unit tests for TaskAgent.

Tests task decomposition, planning, dependency management,
and execution coordination following AGENTS.md guidelines.
"""

from unittest.mock import Mock, patch

import pytest

from omnidev.agents.task_agent import TaskAgent
from omnidev.core.config import ConfigManager


class TestTaskAgent:
    """Test cases for TaskAgent."""

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
    def task_agent(self, mock_config: ConfigManager) -> TaskAgent:
        """Create a TaskAgent instance.

        Args:
            mock_config: Mock ConfigManager fixture.

        Returns:
            TaskAgent instance.
        """
        with patch("omnidev.agents.task_agent.BaseOmniDevAgent.__init__") as mock_init:
            mock_init.return_value = None
            agent = TaskAgent.__new__(TaskAgent)
            object.__setattr__(agent, "config", mock_config)
            return agent

    def test_agent_initialization(self, mock_config: ConfigManager) -> None:
        """Test TaskAgent initialization.

        Args:
            mock_config: Mock ConfigManager fixture.
        """
        with patch("omnidev.agents.task_agent.BaseOmniDevAgent.__init__") as mock_init:
            mock_init.return_value = None
            agent = TaskAgent.__new__(TaskAgent)
            object.__setattr__(agent, "config", mock_config)
            
            assert agent.config == mock_config

    def test_decompose_task_returns_structure(self, task_agent: TaskAgent) -> None:
        """Test decompose_task returns proper structure.

        Args:
            task_agent: TaskAgent fixture.
        """
        result = task_agent.decompose_task("test task")
        
        assert isinstance(result, dict)
        assert "task" in result
        assert "steps" in result
        assert "estimated_complexity" in result
        assert "dependencies" in result

    def test_decompose_task_preserves_task(self, task_agent: TaskAgent) -> None:
        """Test decompose_task preserves original task.

        Args:
            task_agent: TaskAgent fixture.
        """
        task = "Create a new feature"
        result = task_agent.decompose_task(task)
        
        assert result["task"] == task

    def test_decompose_task_structure_types(self, task_agent: TaskAgent) -> None:
        """Test decompose_task returns correct types.

        Args:
            task_agent: TaskAgent fixture.
        """
        result = task_agent.decompose_task("test task")
        
        assert isinstance(result["task"], str)
        assert isinstance(result["steps"], list)
        assert isinstance(result["estimated_complexity"], str)
        assert isinstance(result["dependencies"], list)

    def test_decompose_task_with_different_tasks(self, task_agent: TaskAgent) -> None:
        """Test decompose_task handles different task types.

        Args:
            task_agent: TaskAgent fixture.
        """
        tasks = [
            "Create a new file",
            "Refactor existing code",
            "Fix a bug",
            "Add documentation",
        ]
        
        for task in tasks:
            result = task_agent.decompose_task(task)
            assert result["task"] == task
            assert "steps" in result

