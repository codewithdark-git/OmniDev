"""
Slash command system for OmniDev CLI.

Handles slash commands like /help, /exit, /config, etc.
Works in both interactive and command-line modes.
"""

from typing import Any, Callable, Optional

from rich.console import Console
from rich.table import Table

from omnidev.cli.ui.components import StatusBar

console = Console()


class SlashCommand:
    """Represents a slash command."""

    def __init__(
        self,
        name: str,
        handler: Callable,
        description: str,
        usage: Optional[str] = None,
        aliases: Optional[list[str]] = None,
    ) -> None:
        """Initialize slash command.

        Args:
            name: Command name (without slash).
            handler: Command handler function.
            description: Command description.
            usage: Usage example.
            aliases: Command aliases.
        """
        self.name = name
        self.handler = handler
        self.description = description
        self.usage = usage or f"/{name}"
        self.aliases = aliases or []


class SlashCommandRegistry:
    """Registry for slash commands."""

    def __init__(self) -> None:
        """Initialize command registry."""
        self.commands: dict[str, SlashCommand] = {}
        self._register_default_commands()

    def register(self, command: SlashCommand) -> None:
        """Register a slash command.

        Args:
            command: SlashCommand instance.
        """
        self.commands[command.name] = command
        # Register aliases
        for alias in command.aliases:
            self.commands[alias] = command

    def get(self, name: str) -> Optional[SlashCommand]:
        """Get a command by name.

        Args:
            name: Command name (with or without slash).

        Returns:
            SlashCommand if found, None otherwise.
        """
        # Remove leading slash if present
        name = name.lstrip("/")
        return self.commands.get(name)

    def list_all(self) -> list[SlashCommand]:
        """List all registered commands.

        Returns:
            List of SlashCommand instances.
        """
        # Return unique commands (avoid duplicates from aliases)
        seen = set()
        commands = []
        for cmd in self.commands.values():
            if cmd.name not in seen:
                seen.add(cmd.name)
                commands.append(cmd)
        return commands

    def _register_default_commands(self) -> None:
        """Register default slash commands."""
        # Help command
        self.register(
            SlashCommand(
                "help",
                self._help_handler,
                "Show all available commands",
                usage="/help [command]",
            )
        )
        
        # Exit command
        self.register(
            SlashCommand(
                "exit",
                self._exit_handler,
                "Exit interactive mode",
                aliases=["quit"],
            )
        )
        
        # Clear command
        self.register(
            SlashCommand(
                "clear",
                self._clear_handler,
                "Clear the screen",
            )
        )
        
        # Status command
        self.register(
            SlashCommand(
                "status",
                self._status_handler,
                "Show current status",
            )
        )

    def _help_handler(self, args: list[str], context: Any = None) -> str:
        """Handle /help command.

        Args:
            args: Command arguments.
            context: Optional context object.

        Returns:
            Help text.
        """
        if args:
            # Show help for specific command
            cmd = self.get(args[0])
            if cmd:
                table = Table(title=f"Help: /{cmd.name}")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Description", cmd.description)
                table.add_row("Usage", cmd.usage)
                if cmd.aliases:
                    table.add_row("Aliases", ", ".join(f"/{a}" for a in cmd.aliases))
                
                console.print(table)
                return ""
            else:
                console.print(f"[red]Unknown command: /{args[0]}[/red]")
                return ""
        
        # Show all commands
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Usage", style="yellow")
        
        for cmd in sorted(self.list_all(), key=lambda x: x.name):
            table.add_row(f"/{cmd.name}", cmd.description, cmd.usage)
        
        console.print(table)
        return ""

    def _exit_handler(self, args: list[str], context: Any = None) -> str:
        """Handle /exit command.

        Args:
            args: Command arguments.
            context: Optional context object.

        Returns:
            "exit" to signal exit.
        """
        return "exit"

    def _clear_handler(self, args: list[str], context: Any = None) -> str:
        """Handle /clear command.

        Args:
            args: Command arguments.
            context: Optional context object.

        Returns:
            Empty string.
        """
        console.clear()
        return ""

    def _status_handler(self, args: list[str], context: Any = None) -> str:
        """Handle /status command.

        Args:
            args: Command arguments.
            context: Optional context object with status info.

        Returns:
            Empty string.
        """
        if context:
            # Use context to get status
            files_indexed = getattr(context, "files_indexed", 0)
            providers = getattr(context, "providers", 0)
            mode = getattr(context, "mode", "auto")
            mcp_servers = getattr(context, "mcp_servers", 0)
        else:
            files_indexed = 0
            providers = 0
            mode = "auto"
            mcp_servers = 0
        
        StatusBar(
            files_indexed=files_indexed,
            providers=providers,
            mode=mode,
            mcp_servers=mcp_servers,
        ).render()
        return ""

    def execute(self, command: str, context: Any = None) -> Optional[str]:
        """Execute a slash command.

        Args:
            command: Command string (e.g., "/help" or "/help config").
            context: Optional context object.

        Returns:
            Command result, or None if command not found.
        """
        if not command.startswith("/"):
            return None
        
        parts = command[1:].split(maxsplit=1)
        cmd_name = parts[0]
        args = parts[1].split() if len(parts) > 1 else []
        
        cmd = self.get(cmd_name)
        if cmd:
            return cmd.handler(args, context)
        
        console.print(f"[red]Unknown command: /{cmd_name}[/red]")
        console.print("[dim]Use /help to see available commands[/dim]")
        return None

