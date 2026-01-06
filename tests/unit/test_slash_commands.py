"""Unit tests for slash commands."""

import pytest

from omnidev.cli.commands.slash import SlashCommand, SlashCommandRegistry


class TestSlashCommands:
    """Test cases for slash commands."""

    def test_command_registry(self) -> None:
        """Test command registry."""
        registry = SlashCommandRegistry()
        
        # Test default commands exist
        assert registry.get("help") is not None
        assert registry.get("exit") is not None
        assert registry.get("clear") is not None
        assert registry.get("status") is not None

    def test_register_command(self) -> None:
        """Test registering a custom command."""
        registry = SlashCommandRegistry()
        
        def test_handler(args: list[str], context=None) -> str:
            return "test"
        
        cmd = SlashCommand(
            "test",
            test_handler,
            "Test command",
            usage="/test",
        )
        registry.register(cmd)
        
        assert registry.get("test") == cmd

    def test_execute_command(self) -> None:
        """Test executing a command."""
        registry = SlashCommandRegistry()
        
        # Test help command
        result = registry.execute("/help")
        assert result == ""

