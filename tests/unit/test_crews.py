"""
Unit tests for OmniDevCrews.

Tests crew definitions, task delegation, agent coordination,
and workflow execution following AGENTS.md guidelines.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from omnidev.agents.crews import OmniDevCrews
from omnidev.context.manager import ContextManager
from omnidev.core.config import ConfigManager
from omnidev.models.registry import ProviderRegistry


class TestOmniDevCrews:
    """Test cases for OmniDevCrews."""

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
        return Mock(spec=ContextManager)

    @pytest.fixture
    def mock_provider_registry(self) -> ProviderRegistry:
        """Create a mock ProviderRegistry.

        Returns:
            Mock ProviderRegistry instance.
        """
        return Mock(spec=ProviderRegistry)

    @pytest.fixture
    def crews(
        self,
        mock_config: ConfigManager,
        project_root: Path,
        mock_context_manager: ContextManager,
        mock_provider_registry: ProviderRegistry,
    ) -> OmniDevCrews:
        """Create an OmniDevCrews instance.

        Args:
            mock_config: Mock ConfigManager fixture.
            project_root: Project root fixture.
            mock_context_manager: Mock ContextManager fixture.
            mock_provider_registry: Mock ProviderRegistry fixture.

        Returns:
            OmniDevCrews instance.
        """
        with patch("omnidev.agents.crews.FileProcessingAgent"), \
             patch("omnidev.agents.crews.ContextAgent"), \
             patch("omnidev.agents.crews.RouterAgent"), \
             patch("omnidev.agents.crews.TaskAgent"), \
             patch("omnidev.agents.crews.ValidatorAgent"):
            crews_instance = OmniDevCrews(
                mock_config,
                project_root,
                mock_context_manager,
                mock_provider_registry,
            )
            # Mock agents
            crews_instance.file_agent = Mock()
            crews_instance.context_agent = Mock()
            crews_instance.router_agent = Mock()
            crews_instance.task_agent = Mock()
            crews_instance.validator_agent = Mock()
            return crews_instance

    def test_crews_initialization(
        self,
        mock_config: ConfigManager,
        project_root: Path,
        mock_context_manager: ContextManager,
        mock_provider_registry: ProviderRegistry,
    ) -> None:
        """Test OmniDevCrews initialization.

        Args:
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
            crews_instance = OmniDevCrews(
                mock_config,
                project_root,
                mock_context_manager,
                mock_provider_registry,
            )
            
            assert crews_instance.config == mock_config
            assert crews_instance.project_root == project_root
            assert crews_instance.context_manager == mock_context_manager
            assert crews_instance.provider_registry == mock_provider_registry

    def test_create_code_generation_crew(self, crews: OmniDevCrews) -> None:
        """Test creating code generation crew.

        Args:
            crews: OmniDevCrews fixture.
        """
        with patch("omnidev.agents.crews.Crew") as mock_crew_class, \
             patch("omnidev.agents.crews.Task"):
            crew = crews.create_code_generation_crew()
            
            # Verify crew was created
            assert crew is not None

    def test_create_code_generation_crew_agents(self, crews: OmniDevCrews) -> None:
        """Test code generation crew includes correct agents.

        Args:
            crews: OmniDevCrews fixture.
        """
        with patch("omnidev.agents.crews.Crew") as mock_crew_class, \
             patch("omnidev.agents.crews.Task"):
            crews.create_code_generation_crew()
            
            # Verify Crew was called with correct agents
            call_kwargs = mock_crew_class.call_args[1]
            agents = call_kwargs["agents"]
            assert crews.task_agent in agents
            assert crews.context_agent in agents
            assert crews.router_agent in agents

    def test_create_file_operation_crew(self, crews: OmniDevCrews) -> None:
        """Test creating file operation crew.

        Args:
            crews: OmniDevCrews fixture.
        """
        with patch("omnidev.agents.crews.Crew") as mock_crew_class, \
             patch("omnidev.agents.crews.Task"):
            crew = crews.create_file_operation_crew()
            
            # Verify crew was created
            assert crew is not None

    def test_create_file_operation_crew_agents(self, crews: OmniDevCrews) -> None:
        """Test file operation crew includes correct agents.

        Args:
            crews: OmniDevCrews fixture.
        """
        with patch("omnidev.agents.crews.Crew") as mock_crew_class, \
             patch("omnidev.agents.crews.Task"):
            crews.create_file_operation_crew()
            
            # Verify Crew was called with correct agents
            call_kwargs = mock_crew_class.call_args[1]
            agents = call_kwargs["agents"]
            assert crews.file_agent in agents
            assert crews.validator_agent in agents

    def test_crews_agent_initialization(
        self,
        mock_config: ConfigManager,
        project_root: Path,
        mock_context_manager: ContextManager,
        mock_provider_registry: ProviderRegistry,
    ) -> None:
        """Test agents are initialized in crews.

        Args:
            mock_config: Mock ConfigManager fixture.
            project_root: Project root fixture.
            mock_context_manager: Mock ContextManager fixture.
            mock_provider_registry: Mock ProviderRegistry fixture.
        """
        with patch("omnidev.agents.crews.FileProcessingAgent") as mock_file_agent, \
             patch("omnidev.agents.crews.ContextAgent") as mock_context_agent, \
             patch("omnidev.agents.crews.RouterAgent") as mock_router_agent, \
             patch("omnidev.agents.crews.TaskAgent") as mock_task_agent, \
             patch("omnidev.agents.crews.ValidatorAgent") as mock_validator_agent:
            OmniDevCrews(
                mock_config,
                project_root,
                mock_context_manager,
                mock_provider_registry,
            )
            
            # Verify all agents were initialized
            mock_file_agent.assert_called_once()
            mock_context_agent.assert_called_once()
            mock_router_agent.assert_called_once()
            mock_task_agent.assert_called_once()
            mock_validator_agent.assert_called_once()

