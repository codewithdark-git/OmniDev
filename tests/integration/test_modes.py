"""Integration tests for operational modes."""

import tempfile
from pathlib import Path

import pytest

from omnidev.context.manager import ContextManager
from omnidev.core.config import ConfigManager
from omnidev.core.session import SessionManager
from omnidev.modes.agent import AgentMode
from omnidev.modes.auto_select import AutoSelectMode
from omnidev.models.registry import ProviderRegistry
from omnidev.models.router import ModelRouter


class TestModesIntegration:
    """Integration tests for modes."""

    @pytest.fixture
    def setup_components(self) -> tuple[Path, ConfigManager, SessionManager, ContextManager, ModelRouter]:
        """Setup test components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = ConfigManager(project_root)
            config.load()

            session_manager = SessionManager(project_root, config)
            session_manager.create_session()

            context_manager = ContextManager(project_root, config)

            provider_registry = ProviderRegistry(config)
            model_router = ModelRouter(provider_registry, config)

            return project_root, config, session_manager, context_manager, model_router

    @pytest.mark.asyncio
    async def test_agent_mode_initialization(self, setup_components: tuple) -> None:
        """Test Agent Mode initialization."""
        project_root, config, session_manager, context_manager, model_router = setup_components

        mode = AgentMode(
            project_root,
            config,
            session_manager,
            context_manager,
            model_router,
        )

        assert mode is not None

    @pytest.mark.asyncio
    async def test_auto_select_mode_initialization(self, setup_components: tuple) -> None:
        """Test Auto-Select Mode initialization."""
        project_root, config, session_manager, context_manager, model_router = setup_components

        mode = AutoSelectMode(
            project_root,
            config,
            session_manager,
            context_manager,
            model_router,
        )

        assert mode is not None

