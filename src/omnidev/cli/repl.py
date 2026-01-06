"""
Interactive REPL mode for OmniDev.

Provides a rich interactive shell with command history,
auto-completion, setup wizard, and a status bar.
"""

import asyncio
from pathlib import Path
from typing import Any, Callable, Optional

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from omnidev.core.config import ConfigManager
from omnidev.core.logger import get_logger

console = Console()
logger = get_logger("repl")


# Custom prompt style with gradient colors
PROMPT_STYLE = Style.from_dict({
    "prompt": "bold #00d4ff",
    "prompt-arrow": "bold #ff6ec7",
    "bottom-toolbar": "bg:#1e1e2e #888899",
})


# Available providers with their models
PROVIDER_MODELS = {
    "groq": {
        "name": "Groq (Free)",
        "models": [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "openai/gpt-oss-safeguard-20b",
            "moonshotai/kimi-k2-instruct-0905",
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "meta-llama/llama-guard-4-12b"
            ],
        "requires_key": True,
    },
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4o", "gpt-4-turbo", "gpt-4o-mini", "gpt-3.5-turbo"],
        "requires_key": True,
    },
    "anthropic": {
        "name": "Anthropic",
        "models": ["claude-sonnet-4", "claude-opus-4", "claude-haiku-4"],
        "requires_key": True,
    },
    "google": {
        "name": "Google",
        "models": ["gemini-2.0-flash", "gemini-2.5-pro", "gemini-pro"],
        "requires_key": True,
    },
    "openrouter": {
        "name": "OpenRouter",
        "models": ["openai/gpt-4o", "anthropic/claude-sonnet-4", "google/gemini-2.0-flash"],
        "requires_key": True,
    },
}

# Available modes
MODES = {
    "auto": "Auto-Select - Intelligently selects best approach",
    "agent": "Agent Mode - Full autonomy",
    "planning": "Planning Mode - Shows plan first",
    "manual": "Manual Mode - Approve every step",
}


class OmniDevREPL:
    """Interactive REPL for OmniDev with enhanced features."""

    # Slash commands available in REPL
    SLASH_COMMANDS = {
        "/help": "Show all available commands",
        "/setup": "Run full setup wizard",
        "/provider": "Change AI provider",
        "/model": "Change AI model",
        "/mode": "Change operational mode",
        "/status": "Show current configuration",
        "/history": "Show conversation history",
        "/clear": "Clear the screen",
        "/reset": "Reset conversation history",
        "/exit": "Exit the REPL",
    }

    def __init__(
        self,
        config: ConfigManager,
        project_root: Path,
        execute_callback: Callable[[str, str, Optional[str]], Any],
        provider_registry: Optional[Any] = None,
    ) -> None:
        """Initialize the REPL.

        Args:
            config: Configuration manager.
            project_root: Project root directory.
            execute_callback: Async callback to execute queries (query, mode, provider).
            provider_registry: Optional provider registry for live provider updates.
        """
        self.config = config
        self.project_root = project_root
        self.execute_callback = execute_callback
        self.provider_registry = provider_registry
        
        # Get current settings
        cfg = config.get_config()
        self.current_model = cfg.models.preferred or "auto"
        self.current_provider = cfg.models.fallback or ""
        self.current_mode = cfg.mode.default_mode or "auto"
        
        # Track if provider changed (need to re-register)
        self._provider_changed = False
        
        # Conversation history for context
        self.conversation: list[dict[str, str]] = []
        
        # History file for prompt_toolkit
        history_dir = project_root / ".omnidev"
        history_dir.mkdir(exist_ok=True)
        self.history_file = history_dir / "repl_history"
        
        # Setup key bindings
        self.bindings = self._create_key_bindings()
        
        # Flag to exit
        self._running = True

    def _create_key_bindings(self) -> KeyBindings:
        """Create custom key bindings."""
        bindings = KeyBindings()

        @bindings.add("c-c")
        def _ctrl_c(event: Any) -> None:
            """Handle Ctrl+C - cancel current input."""
            event.app.current_buffer.reset()

        @bindings.add("c-d")
        def _ctrl_d(event: Any) -> None:
            """Handle Ctrl+D - exit REPL."""
            self._running = False
            event.app.exit()

        return bindings

    def _get_prompt(self) -> HTML:
        """Get the formatted prompt."""
        return HTML(
            "<prompt>❯</prompt> "
        )

    def _get_bottom_toolbar(self) -> HTML:
        """Get the bottom toolbar content."""
        model_display = self.current_model
        if len(model_display) > 20:
            model_display = model_display[:17] + "..."
        
        provider_display = self.current_provider or "not set"
        
        return HTML(
            f"<bottom-toolbar>"
            f" <b style='color: #00d4ff'>⚡ {provider_display}</b>"
            f" │ <b style='color: #ff6ec7'>{model_display}</b>"
            f" │ <i>{self.current_mode}</i>"
            f" │ /help"
            f"</bottom-toolbar>"
        )

    def _show_welcome(self) -> None:
        """Show welcome message with current status."""
        # Create a styled welcome box
        welcome_content = Text()
        welcome_content.append("Welcome to ", style="dim")
        welcome_content.append("OmniDev", style="bold bright_blue")
        welcome_content.append(" Interactive Mode\n\n", style="dim")
        
        # Show current config
        if self.current_provider:
            welcome_content.append("  ⚡ Provider: ", style="dim")
            welcome_content.append(f"{self.current_provider}\n", style="bold cyan")
            welcome_content.append("  🤖 Model:    ", style="dim")
            welcome_content.append(f"{self.current_model}\n", style="bold magenta")
            welcome_content.append("  📋 Mode:     ", style="dim")
            welcome_content.append(f"{self.current_mode}\n", style="bold green")
        else:
            welcome_content.append("  ⚠️  ", style="yellow")
            welcome_content.append("No provider configured\n", style="yellow")
            welcome_content.append("     Run ", style="dim")
            welcome_content.append("/setup", style="bold cyan")
            welcome_content.append(" to get started\n", style="dim")
        
        welcome_content.append("\n  Type ", style="dim")
        welcome_content.append("/help", style="bold cyan")
        welcome_content.append(" for commands, or start chatting!", style="dim")
        
        panel = Panel(
            welcome_content,
            border_style="bright_blue",
            padding=(1, 2),
        )
        console.print(panel)
        console.print()

    def _handle_slash_command(self, command: str) -> Optional[str]:
        """Handle a slash command."""
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if cmd in ("/exit", "/quit", "/q"):
            self._running = False
            return None

        elif cmd == "/help":
            self._show_help()
            return ""

        elif cmd == "/clear":
            console.clear()
            self._show_welcome()
            return ""

        elif cmd == "/reset":
            self.conversation = []
            return "✓ Conversation history cleared"

        elif cmd == "/setup":
            self._run_setup()
            return ""

        elif cmd == "/provider":
            self._select_provider()
            return ""

        elif cmd == "/model":
            self._select_model()
            return ""

        elif cmd == "/mode":
            self._select_mode()
            return ""

        elif cmd == "/status":
            self._show_status()
            return ""

        elif cmd == "/history":
            self._show_history()
            return ""

        else:
            return f"[yellow]Unknown command: {cmd}[/yellow]\nType /help for available commands."

    def _show_help(self) -> None:
        """Show help information with styled table."""
        console.print()
        
        # Create commands table
        table = Table(
            title="[bold bright_blue]📚 Available Commands[/bold bright_blue]",
            show_header=True,
            header_style="bold cyan",
            border_style="dim",
            padding=(0, 1),
        )
        table.add_column("Command", style="bold")
        table.add_column("Description", style="dim")
        
        for cmd, desc in self.SLASH_COMMANDS.items():
            table.add_row(cmd, desc)
        
        console.print(table)
        
        # Tips section
        tips = Text()
        tips.append("\n💡 Tips:\n", style="bold")
        tips.append("  • Type your message and press ", style="dim")
        tips.append("Enter", style="bold")
        tips.append(" to send\n", style="dim")
        tips.append("  • Use ", style="dim")
        tips.append("↑/↓", style="bold")
        tips.append(" arrows for command history\n", style="dim")
        tips.append("  • Press ", style="dim")
        tips.append("Ctrl+C", style="bold")
        tips.append(" to cancel, ", style="dim")
        tips.append("Ctrl+D", style="bold")
        tips.append(" to exit\n", style="dim")
        console.print(tips)

    def _run_setup(self) -> None:
        """Run the full setup wizard from within REPL."""
        console.print()
        console.print("[bold bright_blue]🔧 OmniDev Setup Wizard[/bold bright_blue]")
        console.print("[dim]─" * 40 + "[/dim]\n")
        
        # Step 1: Select Provider
        self._select_provider()
        
        if not self.current_provider:
            console.print("[yellow]Setup cancelled.[/yellow]")
            return
        
        # Step 2: Select Model
        self._select_model()
        
        # Step 3: Select Mode
        self._select_mode()
        
        # Step 4: Configure API Key (if needed)
        provider_info = PROVIDER_MODELS.get(self.current_provider)
        if provider_info and provider_info.get("requires_key"):
            existing_key = self.config.get_api_key(self.current_provider)
            if not existing_key:
                self._configure_api_key()
        
        # Save configuration
        self._save_config()
        
        console.print()
        console.print("[bold green]✓ Setup complete![/bold green]")
        self._show_status()

    def _select_provider(self) -> None:
        """Interactive provider selection."""
        console.print()
        console.print("[bold]Select AI Provider:[/bold]\n")
        
        # Build options list
        providers = list(PROVIDER_MODELS.keys())
        for i, provider in enumerate(providers, 1):
            info = PROVIDER_MODELS[provider]
            name = info["name"]
            current = " [green]← current[/green]" if provider == self.current_provider else ""
            console.print(f"  [cyan]{i}[/cyan]. {name}{current}")
        
        console.print(f"  [cyan]0[/cyan]. Cancel")
        console.print()
        
        try:
            choice = click.prompt(
                "Select provider",
                type=click.IntRange(0, len(providers)),
                default=0,
            )
            if choice == 0:
                return
            
            selected = providers[choice - 1]
            old_provider = self.current_provider
            self.current_provider = selected
            
            # Update model to first available for this provider
            models = PROVIDER_MODELS[selected]["models"]
            if models:
                self.current_model = models[0]
            
            # Mark provider as changed so we re-register on next query
            if old_provider != selected:
                self._provider_changed = True
                # Register the new provider immediately if we have registry access
                if self.provider_registry:
                    self.provider_registry.ensure_provider_registered(selected, priority=0)
            
            console.print(f"[green]✓[/green] Provider: {PROVIDER_MODELS[selected]['name']}")
        except (ValueError, click.Abort):
            return

    def _select_model(self) -> None:
        """Interactive model selection based on current provider."""
        if not self.current_provider:
            console.print("[yellow]Please select a provider first (/provider)[/yellow]")
            return
        
        provider_info = PROVIDER_MODELS.get(self.current_provider)
        if not provider_info:
            console.print(f"[yellow]Unknown provider: {self.current_provider}[/yellow]")
            return
        
        models = provider_info["models"]
        if not models:
            console.print("[yellow]No models available for this provider[/yellow]")
            return
        
        console.print()
        console.print(f"[bold]Select Model for {provider_info['name']}:[/bold]\n")
        
        for i, model in enumerate(models, 1):
            current = " [green]← current[/green]" if model == self.current_model else ""
            console.print(f"  [cyan]{i}[/cyan]. {model}{current}")
        
        console.print(f"  [cyan]0[/cyan]. Cancel")
        console.print()
        
        try:
            choice = click.prompt(
                "Select model",
                type=click.IntRange(0, len(models)),
                default=0,
            )
            if choice == 0:
                return
            
            self.current_model = models[choice - 1]
            console.print(f"[green]✓[/green] Model: {self.current_model}")
        except (ValueError, click.Abort):
            return

    def _select_mode(self) -> None:
        """Interactive mode selection."""
        console.print()
        console.print("[bold]Select Operational Mode:[/bold]\n")
        
        modes = list(MODES.keys())
        for i, mode in enumerate(modes, 1):
            desc = MODES[mode]
            current = " [green]← current[/green]" if mode == self.current_mode else ""
            console.print(f"  [cyan]{i}[/cyan]. [bold]{mode}[/bold] - {desc}{current}")
        
        console.print(f"  [cyan]0[/cyan]. Cancel")
        console.print()
        
        try:
            choice = click.prompt(
                "Select mode",
                type=click.IntRange(0, len(modes)),
                default=0,
            )
            if choice == 0:
                return
            
            self.current_mode = modes[choice - 1]
            console.print(f"[green]✓[/green] Mode: {self.current_mode}")
        except (ValueError, click.Abort):
            return

    def _configure_api_key(self) -> None:
        """Configure API key for the current provider."""
        console.print()
        console.print(f"[bold]Configure API Key for {self.current_provider}:[/bold]\n")
        
        # Show where to get the key
        key_urls = {
            "groq": "https://console.groq.com",
            "openai": "https://platform.openai.com/api-keys",
            "anthropic": "https://console.anthropic.com",
            "google": "https://aistudio.google.com/apikey",
            "openrouter": "https://openrouter.ai/keys",
        }
        
        url = key_urls.get(self.current_provider)
        if url:
            console.print(f"  Get your API key from: [link={url}]{url}[/link]\n")
        
        try:
            api_key = click.prompt(
                "Enter API key",
                type=str,
                hide_input=True,
            )
            
            if not api_key or not api_key.strip():
                console.print("[yellow]Skipped - no API key entered[/yellow]")
                return
            
            # Store the API key
            self.config.set_api_key_to_env(self.current_provider, api_key)
            console.print(f"[green]✓[/green] API key saved to .env file")
            
        except (ValueError, click.Abort):
            console.print("[yellow]Skipped[/yellow]")

    def _save_config(self) -> None:
        """Save current settings to config file."""
        try:
            cfg = self.config.get_config()
            cfg.models.preferred = self.current_model
            cfg.models.fallback = self.current_provider
            cfg.mode.default_mode = self.current_mode
            self.config.save_project_config(cfg)
            
            # Mark provider as changed so it gets re-registered
            self._provider_changed = True
            
            # Register the provider immediately if we have registry access
            if self.provider_registry and self.current_provider:
                self.provider_registry.ensure_provider_registered(self.current_provider, priority=0)
        except Exception as e:
            logger.warning(f"Failed to save config: {e}")

    def _show_status(self) -> None:
        """Show current status with styled panel."""
        console.print()
        
        # Build status content
        status = Text()
        status.append("📊 Current Configuration\n\n", style="bold bright_blue")
        
        status.append("  Provider   ", style="dim")
        if self.current_provider:
            pname = PROVIDER_MODELS.get(self.current_provider, {}).get("name", self.current_provider)
            status.append(f"{pname}\n", style="bold cyan")
        else:
            status.append("Not configured\n", style="yellow")
        
        status.append("  Model      ", style="dim")
        status.append(f"{self.current_model}\n", style="bold magenta")
        
        status.append("  Mode       ", style="dim")
        status.append(f"{self.current_mode}\n", style="bold green")
        
        status.append("  Project    ", style="dim")
        status.append(f"{self.project_root.name}\n", style="")
        
        status.append("  Messages   ", style="dim")
        status.append(f"{len(self.conversation)}\n", style="")
        
        # Check API key status
        if self.current_provider:
            has_key = bool(self.config.get_api_key(self.current_provider))
            status.append("\n  API Key    ", style="dim")
            if has_key:
                status.append("✓ Configured\n", style="green")
            else:
                status.append("✗ Not set\n", style="red")
        
        panel = Panel(status, border_style="dim", padding=(0, 2))
        console.print(panel)

    def _show_history(self) -> None:
        """Show conversation history."""
        console.print()
        
        if not self.conversation:
            console.print("[dim]No conversation history yet.[/dim]")
            return

        console.print("[bold]📜 Conversation History[/bold]\n")
        
        for i, msg in enumerate(self.conversation[-10:], 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if len(content) > 80:
                content = content[:77] + "..."
            
            if role == "user":
                console.print(f"  [cyan]You:[/cyan] {content}")
            else:
                console.print(f"  [green]AI:[/green]  {content}")
        
        if len(self.conversation) > 10:
            console.print(f"\n  [dim]... and {len(self.conversation) - 10} more messages[/dim]")

    async def _execute_query(self, query: str) -> None:
        """Execute a query and display the result."""
        # Add to conversation history
        self.conversation.append({"role": "user", "content": query})

        # Show processing indicator with spinner
        provider_name = PROVIDER_MODELS.get(self.current_provider, {}).get("name", self.current_provider)
        console.print()

        try:
            # Pass provider if it was changed so the callback can re-register it
            provider_to_use = self.current_provider if self._provider_changed else None
            
            # Create a spinner for loading indication
            spinner_text = Text()
            spinner_text.append("💭 ", style="")
            spinner_text.append("Thinking", style="bold cyan")
            spinner_text.append(f" with ", style="dim")
            spinner_text.append(f"{self.current_model}", style="bold magenta")
            spinner_text.append(f" via ", style="dim")
            spinner_text.append(f"{provider_name}", style="bold blue")
            spinner_text.append("...", style="dim")
            
            # Use Live context for animated spinner
            with Live(
                Spinner("dots", text=spinner_text, style="cyan"),
                console=console,
                refresh_per_second=10,
                transient=True,  # Remove spinner when done
            ):
                # Execute the query using callback
                result = await self.execute_callback(query, self.current_mode, provider_to_use)
            
            # Reset the flag after successful execution
            self._provider_changed = False

            if isinstance(result, dict):
                if result.get("success"):
                    response = result.get("response", "")
                    # Render response in a styled panel
                    console.print(Panel(
                        Markdown(response),
                        border_style="green",
                        padding=(1, 2),
                    ))
                    self.conversation.append({"role": "assistant", "content": response})
                else:
                    error_msg = result.get("error", "Unknown error")
                    # Extract meaningful error message (avoid showing HTML)
                    if "<!DOCTYPE" in str(error_msg) or "<html" in str(error_msg):
                        error_msg = "Provider returned an error. The API may be temporarily unavailable."
                    console.print(Panel(
                        f"[red]Error: {error_msg}[/red]",
                        border_style="red",
                        title="[red]Error[/red]",
                    ))
            else:
                console.print(str(result))
        except Exception as e:
            error_msg = str(e)
            # Extract meaningful error message (avoid showing HTML)
            if "<!DOCTYPE" in error_msg or "<html" in error_msg:
                error_msg = "Provider returned an error. The API may be temporarily unavailable."
            console.print(Panel(
                f"[red]{error_msg}[/red]",
                border_style="red",
                title="[red]Error[/red]",
            ))
            logger.error(f"Query execution failed: {e}")

    async def run(self) -> None:
        """Run the REPL loop."""
        # Show welcome message
        self._show_welcome()
        
        # Check if provider is configured, prompt setup if not
        if not self.current_provider:
            if click.confirm("Would you like to run setup now?", default=True):
                self._run_setup()
        
        # Create prompt session
        session: PromptSession[str] = PromptSession(
            history=FileHistory(str(self.history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            style=PROMPT_STYLE,
            key_bindings=self.bindings,
        )

        while self._running:
            try:
                # Get user input
                user_input = await session.prompt_async(
                    self._get_prompt(),
                    bottom_toolbar=self._get_bottom_toolbar,
                )

                # Skip empty input
                if not user_input or not user_input.strip():
                    continue

                user_input = user_input.strip()

                # Handle slash commands
                if user_input.startswith("/"):
                    result = self._handle_slash_command(user_input)
                    if result is None:
                        break  # Exit command
                    if result:
                        console.print(result)
                    continue

                # Execute query
                await self._execute_query(user_input)

            except KeyboardInterrupt:
                # Ctrl+C - just clear and continue
                console.print()
                continue
            except EOFError:
                # Ctrl+D - exit
                break
            except Exception as e:
                logger.error(f"REPL error: {e}")
                console.print(f"[red]Error: {e}[/red]")

        console.print()
        console.print("[dim]👋 Goodbye![/dim]")
        console.print()
