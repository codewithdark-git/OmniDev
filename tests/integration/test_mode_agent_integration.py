"""
Integration tests for mode-agent integration.

Tests agent mode and planning mode with agents,
following AGENTS.md guidelines.
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from omnidev.agents.manager import AgentManager
from omnidev.context.manager import ContextManager
from omnidev.core.config import ConfigManager
from omnidev.modes.agent import AgentMode
from omnidev.modes.planning import PlanningMode
from omnidev.models.router import ModelRouter
from omnidev.models.registry import ProviderRegistry
from omnidev.core.session import SessionManager


class TestModeAgentIntegration:
    """Integration tests for mode-agent integration."""

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
    def mock_session_manager(self) -> SessionManager:
        """Create a mock SessionManager.

        Returns:
            Mock SessionManager instance.
        """
        return Mock(spec=SessionManager)

    @pytest.fixture
    def mock_context_manager(self) -> ContextManager:
        """Create a mock ContextManager.

        Returns:
            Mock ContextManager instance.
        """
        context_manager = Mock(spec=ContextManager)
        context_manager.get_context = Mock(return_value={})
        context_manager.build_context = Mock(return_value={"files": []})
        return context_manager

    @pytest.fixture
    def mock_model_router(self) -> ModelRouter:
        """Create a mock ModelRouter.

        Returns:
            Mock ModelRouter instance.
        """
        router = Mock(spec=ModelRouter)
        router.route_request = AsyncMock(return_value=Mock(
            content="test response",
            provider="test",
            model="test-model",
        ))
        return router

    @pytest.fixture
    def agent_mode(
        self,
        project_root: Path,
        mock_config: ConfigManager,
        mock_session_manager: SessionManager,
        mock_context_manager: ContextManager,
        mock_model_router: ModelRouter,
    ) -> AgentMode:
        """Create an AgentMode instance.

        Args:
            project_root: Project root fixture.
            mock_config: Mock ConfigManager fixture.
            mock_session_manager: Mock SessionManager fixture.
            mock_context_manager: Mock ContextManager fixture.
            mock_model_router: Mock ModelRouter fixture.

        Returns:
            AgentMode instance.
        """
        return AgentMode(
            project_root,
            mock_config,
            mock_session_manager,
            mock_context_manager,
            mock_model_router,
        )

    @pytest.fixture
    def planning_mode(
        self,
        project_root: Path,
        mock_config: ConfigManager,
        mock_session_manager: SessionManager,
        mock_context_manager: ContextManager,
        mock_model_router: ModelRouter,
    ) -> PlanningMode:
        """Create a PlanningMode instance.

        Args:
            project_root: Project root fixture.
            mock_config: Mock ConfigManager fixture.
            mock_session_manager: Mock SessionManager fixture.
            mock_context_manager: Mock ContextManager fixture.
            mock_model_router: Mock ModelRouter fixture.

        Returns:
            PlanningMode instance.
        """
        return PlanningMode(
            project_root,
            mock_config,
            mock_session_manager,
            mock_context_manager,
            mock_model_router,
        )

    @pytest.mark.asyncio
    async def test_agent_mode_loads_template(
        self,
        agent_mode: AgentMode,
    ) -> None:
        """Test agent mode loads agent mode template.

        Args:
            agent_mode: AgentMode fixture.
        """
        with patch("omnidev.modes.agent.PromptLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load = Mock(return_value="Agent mode template")
            mock_loader_class.return_value = mock_loader
            
            # Execute should load template
            await agent_mode.execute("test query")
            
            # Verify template was loaded
            mock_loader.load.assert_called_with("templates", "agent_mode")

    @pytest.mark.asyncio
    async def test_planning_mode_loads_template(
        self,
        planning_mode: PlanningMode,
    ) -> None:
        """Test planning mode loads planning mode template.

        Args:
            planning_mode: PlanningMode fixture.
        """
        with patch("omnidev.modes.planning.PromptLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load = Mock(return_value="Planning mode template")
            mock_loader_class.return_value = mock_loader
            
            # Execute should load template
            await planning_mode.execute("test query")
            
            # Verify template was loaded
            mock_loader.load.assert_called_with("templates", "planning_mode")

    @pytest.mark.asyncio
    async def test_agent_mode_template_integration(
        self,
        agent_mode: AgentMode,
    ) -> None:
        """Test agent mode integrates template with query.

        Args:
            agent_mode: AgentMode fixture.
        """
        with patch("omnidev.modes.agent.PromptLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load = Mock(return_value="Template content")
            mock_loader_class.return_value = mock_loader
            
            result = await agent_mode.execute("test query")
            
            # Verify result structure
            assert "success" in result or "query" in result

    @pytest.mark.asyncio
    async def test_planning_mode_template_integration(
        self,
        planning_mode: PlanningMode,
    ) -> None:
        """Test planning mode integrates template with query.

        Args:
            planning_mode: PlanningMode fixture.
        """
        with patch("omnidev.modes.planning.PromptLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load = Mock(return_value="Template content")
            mock_loader_class.return_value = mock_loader
            
            result = await planning_mode.execute("test query")
            
            # Verify result structure
            assert "plan" in result or "query" in result

