"""
Interactive terminal mode for OmniDev CLI.

Provides full-screen interactive mode with command history, auto-completion,
and real-time suggestions.
"""

import sys
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console

from omnidev.cli.ui.components import Logo, TipsPanel

console = Console()


class OmniDevCompleter(Completer):
    """Auto-completer for OmniDev commands."""

    def __init__(self, commands: list[str]) -> None:
        """Initialize completer.

        Args:
            commands: List of available commands.
        """
        self.commands = commands

    def get_completions(self, document, complete_event) -> None:
        """Get completions for current input.

        Args:
            document: Current document.
            complete_event: Completion event.
        """
        word = document.get_word_before_cursor()
        
        # Slash command completions
        if document.text.startswith("/"):
            for cmd in self.commands:
                if cmd.startswith(word):
                    yield Completion(cmd, start_position=-len(word))
        else:
            # Regular command completions
            for cmd in self.commands:
                if cmd.startswith(word):
                    yield Completion(cmd, start_position=-len(word))


class InteractiveMode:
    """Interactive terminal mode for OmniDev."""

    def __init__(
        self,
        commands: Optional[list[str]] = None,
        history_file: Optional[str] = None,
    ) -> None:
        """Initialize interactive mode.

        Args:
            commands: List of available commands for completion.
            history_file: Path to history file.
        """
        self.commands = commands or []
        self.history_file = history_file or "~/.omnidev_history"
        
        # Setup history
        self.history = FileHistory(self.history_file)
        
        # Setup completer
        self.completer = OmniDevCompleter(self.commands)
        
        # Setup key bindings
        self.bindings = KeyBindings()
        
        # Create prompt session
        self.session = PromptSession(
            history=self.history,
            completer=self.completer,
            auto_suggest=AutoSuggestFromHistory(),
            key_bindings=self.bindings,
        )

    def show_welcome(self) -> None:
        """Show welcome screen."""
        console.clear()
        Logo.render()
        console.print()
        TipsPanel().render()
        console.print()

    def get_input(self, prompt: str = "omnidev> ") -> str:
        """Get user input.

        Args:
            prompt: Input prompt.

        Returns:
            User input string.
        """
        try:
            return self.session.prompt(prompt)
        except KeyboardInterrupt:
            return "/exit"
        except EOFError:
            return "/exit"

    def run(self, command_handler: callable) -> None:
        """Run interactive mode.

        Args:
            command_handler: Function to handle commands.
        """
        self.show_welcome()
        
        while True:
            try:
                user_input = self.get_input()
                
                if not user_input.strip():
                    continue
                
                # Handle exit
                if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
                    console.print("\n[dim]Goodbye![/dim]")
                    break
                
                # Process command
                result = command_handler(user_input)
                
                if result == "exit":
                    break
                    
            except KeyboardInterrupt:
                console.print("\n[dim]Use /exit to quit[/dim]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

