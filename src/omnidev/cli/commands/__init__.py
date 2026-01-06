"""
CLI commands package for OmniDev.

This package contains command handlers and utilities.
"""

import asyncio
from pathlib import Path
from typing import Optional

import click

from omnidev.actions.backup import BackupManager
from omnidev.actions.file_ops import FileOperations
from omnidev.actions.git_ops import GitOperations
from omnidev.cli.agent_bridge import CLIAgentBridge
from omnidev.cli.commands.slash import SlashCommandRegistry
from omnidev.cli.setup_wizard import SetupWizard
from omnidev.cli.ui.components import ActionBlock, Logo, ResponseHeader, TipsPanel
from rich.console import Console
from omnidev.context.manager import ContextManager
from omnidev.core.config import ConfigManager, ProjectConfig
from omnidev.core.exceptions import ConfigurationError, OmniDevError
from omnidev.core.logger import LoggerManager, get_logger
from omnidev.core.session import SessionManager
from omnidev.modes.agent import AgentMode
from omnidev.modes.auto_select import AutoSelectMode
from omnidev.modes.manual import ManualMode
from omnidev.modes.planning import PlanningMode
from omnidev.models.registry import ProviderRegistry
from omnidev.models.router import ModelRouter


class OmniDevCLI:
    """Main CLI application class."""

    def __init__(self, project_root: Optional[Path] = None) -> None:
        """Initialize the CLI.

        Args:
            project_root: Optional project root directory.
        """
        self.project_root = (project_root or Path.cwd()).resolve()
        self.logger_manager = LoggerManager()
        self.logger = get_logger("cli")

        # Initialize core components
        try:
            self.config = ConfigManager(self.project_root)
            self.config.load()

            self.session_manager = SessionManager(self.project_root, self.config)
            self.session_manager.create_session()

            self.context_manager = ContextManager(self.project_root, self.config)

            # Initialize provider registry and register providers based on config
            self.provider_registry = ProviderRegistry(self.config, auto_register=False)
            # Register providers based on saved configuration
            self._register_configured_providers()
            self.model_router = ModelRouter(self.provider_registry, self.config)
            
            # Initialize agent bridge
            self.agent_bridge = CLIAgentBridge(
                self.config,
                self.project_root,
                self.context_manager,
                self.provider_registry,
            )
            
            # Initialize slash command registry
            self.slash_registry = SlashCommandRegistry()
        except Exception as e:
            self.logger.error(f"Failed to initialize CLI: {e}")
            raise

    def _register_configured_providers(self) -> None:
        """Register ONLY the configured provider.
        
        No automatic fallback - if the provider fails, show error.
        The user explicitly selects which provider to use.
        """
        try:
            config = self.config.get_config()
            configured_provider = config.models.fallback
            
            # Register ONLY the configured provider with priority 0 (highest)
            if configured_provider:
                registered = self.provider_registry.ensure_provider_registered(
                    configured_provider, priority=0
                )
                if not registered:
                    self.logger.warning(
                        f"Failed to register configured provider '{configured_provider}'. "
                        f"Please run 'omnidev setup' to configure a provider."
                    )
            else:
                self.logger.warning(
                    "No provider configured. Run 'omnidev setup' to configure one."
                )
        except Exception as e:
            self.logger.warning(f"Failed to register configured providers: {e}")

    def get_mode(self, mode_name: str) -> Optional[object]:
        """Get a mode instance by name.

        Args:
            mode_name: Mode name (agent, planning, auto, manual).

        Returns:
            Mode instance if found, None otherwise.
        """
        modes = {
            "agent": AgentMode,
            "planning": PlanningMode,
            "auto": AutoSelectMode,
            "manual": ManualMode,
        }

        mode_class = modes.get(mode_name.lower())
        if not mode_class:
            return None

        try:
            return mode_class(
                self.project_root,
                self.config,
                self.session_manager,
                self.context_manager,
                self.model_router,
            )
        except Exception as e:
            self.logger.error(f"Failed to create mode {mode_name}: {e}")
            return None

    async def execute_query(self, query: str, mode: str = "auto", use_agents: bool = True) -> dict:
        """Execute a query in the specified mode.

        Args:
            query: User query.
            mode: Mode name.

        Returns:
            Execution results.
        """
        mode_instance = self.get_mode(mode)
        if not mode_instance:
            raise OmniDevError(f"Invalid mode: {mode}")

        return await mode_instance.execute(query)


# CLI command handlers

cli_instance: Optional[OmniDevCLI] = None


def get_cli() -> OmniDevCLI:
    """Get or create CLI instance.

    Returns:
        CLI instance.
    """
    global cli_instance
    if cli_instance is None:
        cli_instance = OmniDevCLI()
    return cli_instance


@click.command(name="run")
@click.argument("query", required=False)
@click.option("--mode", "-m", help="Operational mode (agent, planning, auto, manual)")
@click.option("--model", help="Specific model to use")
@click.option("--project-root", type=click.Path(exists=True, path_type=Path), help="Project root directory")
@click.option("--setup", is_flag=True, help="Run setup wizard")
@click.option("--interactive", "-i", is_flag=True, help="Start interactive REPL mode")
@click.pass_context
def run_command(
    ctx: click.Context, 
    query: Optional[str], 
    mode: Optional[str], 
    model: Optional[str], 
    project_root: Optional[Path],
    setup: bool,
    interactive: bool
) -> None:
    """OmniDev - Your Multi-Model AI Development Assistant.

    Execute a query or start interactive mode.
    """
    from omnidev.cli.repl import OmniDevREPL
    
    try:
        # Show logo with tagline for startup
        Logo.render_with_tagline()
        
        # Initialize config first (needed for setup wizard)
        config = ConfigManager(project_root or Path.cwd())
        config.load()
        
        # Check if provider is configured
        configured_provider = config.get_config().models.fallback
        if not configured_provider:
            # No provider configured - run setup wizard
            console = Console()
            console.print("[yellow]No provider configured. Starting setup wizard...[/yellow]\n")
            wizard = SetupWizard(config, project_root or Path.cwd())
            setup_result = wizard.run()
            
            if not mode:
                mode = setup_result.get("mode", "auto")
            if not model:
                model = setup_result.get("model")
        
        # Run setup wizard if explicitly requested
        elif setup:
            wizard = SetupWizard(config, project_root or Path.cwd())
            setup_result = wizard.run()
            
            if not mode:
                mode = setup_result.get("mode", "auto")
            if not model:
                model = setup_result.get("model")
        
        # Initialize CLI with project root
        cli = OmniDevCLI(project_root)
        
        # Use default mode if not specified
        if not mode:
            mode = cli.config.get_config().mode.default_mode or "auto"
        
        # Start interactive mode if requested or if no query provided
        if interactive or (not query and not setup):
            TipsPanel().render()
            
            # Define async callback for REPL that re-registers provider before executing
            async def execute_callback(q: str, m: str, provider: str = None) -> dict:
                # Re-register the provider if specified (ensures latest selection is used)
                if provider:
                    cli.provider_registry.ensure_provider_registered(provider, priority=0)
                    # Reload config to get latest settings
                    cli.config.load()
                return await cli.execute_query(q, m, use_agents=True)
            
            # Start REPL with provider registry access
            repl = OmniDevREPL(
                config=cli.config,
                project_root=project_root or Path.cwd(),
                execute_callback=execute_callback,
                provider_registry=cli.provider_registry,
            )
            asyncio.run(repl.run())
            return

        # Execute single query
        if query:
            # Check if it's a slash command
            if query.startswith("/"):
                result = cli.slash_registry.execute(query, cli)
                if result == "exit":
                    return
                if result:
                    click.echo(result)
                return
            
            # Show response header
            current_model = cli.config.get_config().models.preferred or "auto"
            current_provider = cli.config.get_config().models.fallback or "unknown"
            ResponseHeader(current_model, current_provider).render()
            
            # Execute query with agents
            with cli.logger_manager:
                result = asyncio.run(cli.execute_query(query, mode, use_agents=True))
                
                # Show action block
                if result.get("success"):
                    ActionBlock(
                        action="Query executed successfully",
                        content=result.get("response", ""),
                    ).render()
                else:
                    from omnidev.cli.ui.components import ErrorPanel
                    ErrorPanel(Exception(result.get("error", "Unknown error"))).render()
    except KeyboardInterrupt:
        click.echo("\nInterrupted by user", err=True)
    except Exception as e:
        from omnidev.cli.ui.components import ErrorPanel
        ErrorPanel(e).render()
        raise click.Abort()


@click.group()
def config_group() -> None:
    """Configuration management commands."""
    pass


@config_group.command()
@click.argument("key")
@click.argument("value")
def set_config(key: str, value: str) -> None:
    """Set a configuration value."""
    try:
        cli = get_cli()
        config = cli.config.get_config()

        # Update config based on key
        if key == "default-mode":
            config.mode.default_mode = value
        elif key == "default-model":
            config.models.default = value
        elif key.startswith("context."):
            # Handle context config
            pass
        else:
            click.echo(f"Unknown config key: {key}", err=True)
            return

        cli.config.save_global_config(config)
        click.echo(f"Set {key} = {value}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@config_group.command()
@click.argument("provider")
@click.argument("api_key")
def add_key(provider: str, api_key: str) -> None:
    """Add an API key for a provider."""
    try:
        cli = get_cli()
        cli.config.set_api_key(provider, api_key)
        click.echo(f"API key added for {provider}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@config_group.command()
def list_keys() -> None:
    """List stored API keys."""
    try:
        cli = get_cli()
        keys = cli.config.list_api_keys()
        if keys:
            click.echo("Stored API keys:")
            for provider in keys:
                click.echo(f"  - {provider}")
        else:
            click.echo("No API keys stored")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


__all__ = ["OmniDevCLI", "run_command", "config_group", "get_cli"]
