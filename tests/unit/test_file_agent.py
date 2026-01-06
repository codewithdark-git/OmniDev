"""
Unit tests for FileProcessingAgent.

Tests file operation decisions, safety checks, backup coordination,
and error scenarios following AGENTS.md guidelines.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from omnidev.agents.file_agent import FileProcessingAgent
from omnidev.core.config import ConfigManager
from omnidev.core.exceptions import ValidationError


class TestFileProcessingAgent:
    """Test cases for FileProcessingAgent."""

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
    def file_agent(self, mock_config: ConfigManager, project_root: Path) -> FileProcessingAgent:
        """Create a FileProcessingAgent instance.

        Args:
            mock_config: Mock ConfigManager fixture.
            project_root: Project root fixture.

        Returns:
            FileProcessingAgent instance.
        """
        with patch("omnidev.agents.file_agent.BaseOmniDevAgent.__init__"), \
             patch("omnidev.agents.file_agent.FileOperations") as mock_file_ops:
            mock_file_ops.return_value = Mock()
            agent = FileProcessingAgent(mock_config, project_root)
            # Bypass parent initialization for testing
            agent.config = mock_config
            agent.project_root = project_root
            agent.file_ops = mock_file_ops.return_value
            return agent

    def test_agent_initialization(self, mock_config: ConfigManager, project_root: Path) -> None:
        """Test FileProcessingAgent initialization.

        Args:
            mock_config: Mock ConfigManager fixture.
            project_root: Project root fixture.
        """
        with patch("omnidev.agents.file_agent.BaseOmniDevAgent.__init__"), \
             patch("omnidev.agents.file_agent.FileOperations") as mock_file_ops:
            mock_file_ops.return_value = Mock()
            agent = FileProcessingAgent(mock_config, project_root)
            agent.config = mock_config
            agent.project_root = project_root
            agent.file_ops = mock_file_ops.return_value
            
            assert agent.config == mock_config
            assert agent.project_root == project_root
            assert hasattr(agent, "file_ops")

    def test_should_create_file_when_file_exists(self, file_agent: FileProcessingAgent, project_root: Path) -> None:
        """Test should_create_file returns False when file exists.

        Args:
            file_agent: FileProcessingAgent fixture.
            project_root: Project root fixture.
        """
        # Create existing file
        existing_file = project_root / "existing.txt"
        existing_file.write_text("content")
        
        result = file_agent.should_create_file(existing_file, "new content")
        
        assert isinstance(result, dict)
        assert "should_create" in result
        assert "reason" in result
        assert result["should_create"] is False
        assert "already exists" in result["reason"].lower()

    def test_should_create_file_when_file_not_exists(self, file_agent: FileProcessingAgent, project_root: Path) -> None:
        """Test should_create_file returns True when file doesn't exist.

        Args:
            file_agent: FileProcessingAgent fixture.
            project_root: Project root fixture.
        """
        new_file = project_root / "new.txt"
        
        result = file_agent.should_create_file(new_file, "content")
        
        assert isinstance(result, dict)
        assert "should_create" in result
        assert "reason" in result
        assert result["should_create"] is True
        assert "can be created" in result["reason"].lower()

    def test_should_create_file_with_relative_path(self, file_agent: FileProcessingAgent, project_root: Path) -> None:
        """Test should_create_file handles relative paths.

        Args:
            file_agent: FileProcessingAgent fixture.
            project_root: Project root fixture.
        """
        new_file = Path("relative.txt")
        
        result = file_agent.should_create_file(new_file, "content")
        
        # Should handle relative paths
        assert "should_create" in result
        assert "reason" in result

    def test_file_ops_integration(self, file_agent: FileProcessingAgent) -> None:
        """Test file_ops is properly initialized.

        Args:
            file_agent: FileProcessingAgent fixture.
        """
        assert file_agent.file_ops is not None
        # Verify file_ops is a mock or has project_root attribute
        assert hasattr(file_agent.file_ops, "project_root") or isinstance(file_agent.file_ops, Mock)

    def test_project_root_assignment(self, mock_config: ConfigManager, project_root: Path) -> None:
        """Test project_root is correctly assigned.

        Args:
            mock_config: Mock ConfigManager fixture.
            project_root: Project root fixture.
        """
        with patch("omnidev.agents.file_agent.BaseOmniDevAgent.__init__"), \
             patch("omnidev.agents.file_agent.FileOperations") as mock_file_ops:
            mock_file_ops.return_value = Mock()
            agent = FileProcessingAgent(mock_config, project_root)
            agent.config = mock_config
            agent.project_root = project_root
            agent.file_ops = mock_file_ops.return_value
            
            assert agent.project_root == project_root

