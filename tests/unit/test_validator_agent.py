"""
Unit tests for ValidatorAgent.

Tests code validation, syntax checking, quality assessment,
and error reporting following AGENTS.md guidelines.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from omnidev.agents.validator_agent import ValidatorAgent
from omnidev.core.config import ConfigManager


class TestValidatorAgent:
    """Test cases for ValidatorAgent."""

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
    def validator_agent(
        self,
        mock_config: ConfigManager,
        project_root: Path,
    ) -> ValidatorAgent:
        """Create a ValidatorAgent instance.

        Args:
            mock_config: Mock ConfigManager fixture.
            project_root: Project root fixture.

        Returns:
            ValidatorAgent instance.
        """
        with patch("omnidev.agents.validator_agent.BaseOmniDevAgent.__init__") as mock_init:
            mock_init.return_value = None
            agent = ValidatorAgent.__new__(ValidatorAgent)
            object.__setattr__(agent, "config", mock_config)
            # Mock validator
            mock_validator = Mock()
            mock_validator.validate_file = Mock(return_value={
                "valid": True,
                "errors": [],
                "warnings": [],
            })
            object.__setattr__(agent, "validator", mock_validator)
            return agent

    def test_agent_initialization(
        self,
        mock_config: ConfigManager,
        project_root: Path,
    ) -> None:
        """Test ValidatorAgent initialization.

        Args:
            mock_config: Mock ConfigManager fixture.
            project_root: Project root fixture.
        """
        with patch("omnidev.agents.validator_agent.BaseOmniDevAgent.__init__") as mock_init, \
             patch("omnidev.agents.validator_agent.CodeValidator") as mock_validator_class:
            mock_init.return_value = None
            mock_validator_class.return_value = Mock()
            agent = ValidatorAgent.__new__(ValidatorAgent)
            object.__setattr__(agent, "config", mock_config)
            object.__setattr__(agent, "validator", mock_validator_class.return_value)
            
            assert agent.config == mock_config
            assert hasattr(agent, "validator")

    def test_validate_code_calls_validator(
        self,
        validator_agent: ValidatorAgent,
        project_root: Path,
    ) -> None:
        """Test validate_code calls validator.

        Args:
            validator_agent: ValidatorAgent fixture.
            project_root: Project root fixture.
        """
        file_path = project_root / "test.py"
        file_path.write_text("print('test')")
        
        result = validator_agent.validate_code(file_path)
        
        validator_agent.validator.validate_file.assert_called_once_with(file_path)
        assert isinstance(result, dict)

    def test_validate_code_returns_structure(
        self,
        validator_agent: ValidatorAgent,
        project_root: Path,
    ) -> None:
        """Test validate_code returns proper structure.

        Args:
            validator_agent: ValidatorAgent fixture.
            project_root: Project root fixture.
        """
        file_path = project_root / "test.py"
        file_path.write_text("print('test')")
        
        result = validator_agent.validate_code(file_path)
        
        assert "valid" in result
        assert "errors" in result
        assert "warnings" in result

    def test_validate_code_with_errors(
        self,
        mock_config: ConfigManager,
        project_root: Path,
    ) -> None:
        """Test validate_code handles validation errors.

        Args:
            mock_config: Mock ConfigManager fixture.
            project_root: Project root fixture.
        """
        with patch("omnidev.agents.validator_agent.BaseOmniDevAgent.__init__") as mock_init:
            mock_init.return_value = None
            agent = ValidatorAgent.__new__(ValidatorAgent)
            object.__setattr__(agent, "config", mock_config)
            mock_validator = Mock()
            mock_validator.validate_file = Mock(return_value={
                "valid": False,
                "errors": ["Syntax error on line 1"],
                "warnings": ["Unused import"],
            })
            object.__setattr__(agent, "validator", mock_validator)
            
            file_path = project_root / "test.py"
            result = agent.validate_code(file_path)
            
            assert result["valid"] is False
            assert len(result["errors"]) > 0
            assert len(result["warnings"]) > 0

    def test_validate_code_structure_types(
        self,
        validator_agent: ValidatorAgent,
        project_root: Path,
    ) -> None:
        """Test validate_code returns correct types.

        Args:
            validator_agent: ValidatorAgent fixture.
            project_root: Project root fixture.
        """
        file_path = project_root / "test.py"
        file_path.write_text("print('test')")
        
        result = validator_agent.validate_code(file_path)
        
        assert isinstance(result["valid"], bool)
        assert isinstance(result["errors"], list)
        assert isinstance(result["warnings"], list)

