"""Unit tests for CLI module."""

import pytest
from click.testing import CliRunner

from omnidev.cli.main import cli_main


class TestCLI:
    """Test cases for CLI commands."""

    def test_version_command(self) -> None:
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(cli_main, ["version"])
        assert result.exit_code == 0
        assert "OmniDev v0.1.0" in result.output

    def test_setup_command(self) -> None:
        """Test setup command."""
        runner = CliRunner()
        result = runner.invoke(cli_main, ["setup"])
        assert result.exit_code == 0
        assert "OmniDev Setup" in result.output

    def test_main_group(self) -> None:
        """Test main command group."""
        runner = CliRunner()
        result = runner.invoke(cli_main, ["--help"])
        assert result.exit_code == 0
        assert "OmniDev" in result.output

