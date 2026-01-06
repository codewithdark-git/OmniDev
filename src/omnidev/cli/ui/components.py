"""
Rich UI components for OmniDev CLI.

Provides reusable UI components with Rich library for a modern terminal experience.
"""

from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.text import Text

from omnidev.core.exceptions import OmniDevError

console = Console()


class Logo:
    """OmniDev logo component with gradient colors."""

    # Large ASCII art logo - Gemini CLI inspired
    ASCII_ART = r"""
   ____                  _ _____             
  / __ \                (_)  __ \            
 | |  | |_ __ ___  _ __  _| |  | | _____   __
 | |  | | '_ ` _ \| '_ \| | |  | |/ _ \ \ / /
 | |__| | | | | | | | | | | |__| |  __/\ V / 
  \____/|_| |_| |_|_| |_|_|_____/ \___| \_/  
"""

    @staticmethod
    def render(compact: bool = False) -> None:
        """Render the OmniDev logo.
        
        Args:
            compact: If True, show compact version without ASCII art.
        """
        if compact:
            logo_text = Text()
            logo_text.append("> ", style="bold bright_blue")
            logo_text.append("OMNI", style="bold bright_blue")
            logo_text.append("DEV", style="bold bright_magenta")
            console.print(logo_text)
            return

        # Render large ASCII art with gradient
        lines = Logo.ASCII_ART.strip().split("\n")
        
        # Color gradient from blue to magenta
        colors = [
            "#00aaff",  # Bright blue
            "#22aaff",
            "#4499ff",
            "#6688ff",
            "#8877ff",
            "#aa66ff",  # Magenta
        ]
        
        console.print()  # Spacing
        for i, line in enumerate(lines):
            color = colors[i % len(colors)]
            console.print(f"[bold {color}]{line}[/bold {color}]")
        console.print()  # Spacing

    @staticmethod
    def render_with_tagline() -> None:
        """Render logo with tagline for startup."""
        Logo.render()
        tagline = Text()
        tagline.append("  Your ", style="dim")
        tagline.append("Multi-Model", style="bold bright_blue")
        tagline.append(" AI Development Assistant\n", style="dim")
        console.print(tagline)


class TipsPanel:
    """Simplified tips display - Gemini CLI style."""

    def __init__(self, tips: Optional[list[str]] = None) -> None:
        """Initialize tips panel.

        Args:
            tips: List of tip strings. If None, uses default tips.
        """
        self.tips = tips or [
            "Ask questions, edit files, or run commands",
            "Be specific for best results",
            "Use -i or --interactive for chat mode",
            "Type /help for more commands",
        ]

    def render(self, collapsed: bool = False) -> None:
        """Render the tips.

        Args:
            collapsed: Whether to show collapsed version.
        """
        if collapsed:
            console.print("[dim]Type /help for tips[/dim]")
            return

        # Simple numbered list format
        console.print("[bold]Getting started:[/bold]")
        for i, tip in enumerate(self.tips, 1):
            console.print(f"  [dim]{i}.[/dim] [cyan]{tip}[/cyan]")
        console.print()  # Spacing


class ResponseHeader:
    """Shows response attribution - "Responding with {model}..." style."""

    def __init__(self, model: str, provider: Optional[str] = None) -> None:
        """Initialize response header.

        Args:
            model: Model name being used.
            provider: Optional provider name.
        """
        self.model = model
        self.provider = provider

    def render(self) -> None:
        """Render the response header."""
        header = Text()
        header.append("\n")
        if self.provider:
            header.append(f"Responding with ", style="dim")
            header.append(f"{self.model}", style="bold bright_blue")
            header.append(f" via ", style="dim")
            header.append(f"{self.provider}", style="bright_magenta")
        else:
            header.append(f"Responding with ", style="dim")
            header.append(f"{self.model}", style="bold bright_blue")
        header.append("...\n", style="dim")
        console.print(header)


class ActionBlock:
    """Action block showing file operations with syntax highlighting."""

    def __init__(
        self,
        action: str,
        file_path: Optional[Path] = None,
        content: Optional[str] = None,
        language: str = "python",
    ) -> None:
        """Initialize action block.

        Args:
            action: Action description (e.g., "WriteFile Writing to hello.py").
            file_path: Path to the file being acted upon.
            content: File content to display.
            language: Language for syntax highlighting.
        """
        self.action = action
        self.file_path = file_path
        self.content = content
        self.language = language

    def render(self) -> None:
        """Render the action block."""
        # Create action text with checkmark
        action_text = Text()
        action_text.append("✓ ", style="bold green")
        action_text.append(self.action, style="bold")

        # Create content panel if content is provided
        if self.content:
            syntax = Syntax(
                self.content,
                self.language,
                theme="monokai",
                line_numbers=True,
                word_wrap=True,
            )
            panel = Panel(
                syntax,
                title=f"[bold]{self.action}[/bold]",
                border_style="bright_blue",
                padding=(1, 1),
            )
            console.print(panel)
        else:
            console.print(action_text)


class StatusBar:
    """Status bar showing current system state."""

    def __init__(
        self,
        files_indexed: int = 0,
        providers: int = 0,
        mode: str = "auto",
        mcp_servers: int = 0,
    ) -> None:
        """Initialize status bar.

        Args:
            files_indexed: Number of files indexed.
            providers: Number of providers available.
            mode: Current operational mode.
            mcp_servers: Number of MCP servers connected.
        """
        self.files_indexed = files_indexed
        self.providers = providers
        self.mode = mode
        self.mcp_servers = mcp_servers

    def render(self) -> None:
        """Render the status bar."""
        status_parts = []
        
        if self.files_indexed > 0:
            status_parts.append(f"[cyan]{self.files_indexed} files indexed[/cyan]")
        
        if self.providers > 0:
            status_parts.append(f"[green]{self.providers} providers[/green]")
        
        if self.mode:
            status_parts.append(f"[yellow]mode: {self.mode}[/yellow]")
        
        if self.mcp_servers > 0:
            status_parts.append(f"[magenta]{self.mcp_servers} MCP servers[/magenta]")

        if status_parts:
            status_text = " | ".join(status_parts)
            console.print(f"[dim]{status_text}[/dim]")


class ProgressIndicator:
    """Progress indicator for long-running operations."""

    def __init__(self, description: str = "Processing...") -> None:
        """Initialize progress indicator.

        Args:
            description: Description text for the progress.
        """
        self.description = description
        self.progress: Optional[Progress] = None

    def __enter__(self) -> "ProgressIndicator":
        """Context manager entry."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        )
        self.progress.start()
        self.task_id = self.progress.add_task(self.description, total=None)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        if self.progress:
            self.progress.stop()

    def update(self, description: Optional[str] = None) -> None:
        """Update progress description.

        Args:
            description: New description text.
        """
        if self.progress and description:
            self.progress.update(self.task_id, description=description)


class ErrorPanel:
    """Error panel for displaying errors."""

    def __init__(self, error: Exception, title: str = "Error") -> None:
        """Initialize error panel.

        Args:
            error: Exception to display.
            title: Panel title.
        """
        self.error = error
        self.title = title

    def render(self) -> None:
        """Render the error panel."""
        error_message = str(self.error)
        if isinstance(self.error, OmniDevError):
            error_message = self.error.message

        panel = Panel(
            error_message,
            title=f"[bold red]{self.title}[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
        console.print(panel)


class WarningPanel:
    """Warning panel for displaying warnings."""

    def __init__(self, message: str, title: str = "Warning") -> None:
        """Initialize warning panel.

        Args:
            message: Warning message.
            title: Panel title.
        """
        self.message = message
        self.title = title

    def render(self) -> None:
        """Render the warning panel."""
        panel = Panel(
            self.message,
            title=f"[bold yellow]{self.title}[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
        console.print(panel)

