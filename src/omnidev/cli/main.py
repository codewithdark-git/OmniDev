"""
Main CLI entry point for OmniDev.

This module provides the main command-line interface for OmniDev,
handling command parsing and routing to appropriate handlers.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from omnidev.cli.commands import config_group, run_command
from omnidev.core.exceptions import OmniDevError


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="omnidev")
@click.argument("query", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Start interactive REPL mode")
@click.option("--mode", "-m", help="Operational mode (agent, planning, auto, manual)")
@click.option("--model", help="Specific model to use")
@click.option("--project-root", type=click.Path(exists=True, path_type=Path), help="Project root directory")
@click.option("--setup", is_flag=True, help="Run setup wizard")
@click.pass_context
def cli_main(
    ctx: click.Context,
    query: Optional[str],
    interactive: bool,
    mode: Optional[str],
    model: Optional[str],
    project_root: Optional[Path],
    setup: bool,
) -> None:
    """
    OmniDev - Your Multi-Model AI Development Assistant.

    Free, Intelligent, Autonomous AI coding assistant for your terminal.
    """
    # If no command specified, invoke run_command with the options
    if ctx.invoked_subcommand is None:
        ctx.invoke(
            run_command,
            query=query,
            interactive=interactive,
            mode=mode,
            model=model,
            project_root=project_root,
            setup=setup,
        )


# Add commands
cli_main.add_command(run_command, name="run")
cli_main.add_command(config_group, name="config")


@cli_main.command()
def version() -> None:
    """Show OmniDev version information."""
    click.echo("OmniDev v0.1.0")
    click.echo("Your Multi-Model AI Development Assistant")


@cli_main.command()
@click.option("--project-root", type=click.Path(exists=True, path_type=Path), help="Project root directory")
def setup(project_root: Optional[Path]) -> None:
    """Run first-time setup wizard for OpenRouter API key.
    
    This command helps you configure the OpenRouter API key for agent operations.
    The API key will be stored in a project-specific .env file.
    """
    from omnidev.core.config import ConfigManager
    from omnidev.cli.ui.components import Logo
    
    console = Console()
    Logo.render()
    
    console.print("\n[bold cyan]OmniDev Setup Wizard[/bold cyan]")
    console.print("=" * 50)
    console.print("\nThis setup will configure the OpenRouter API key for agent operations.")
    console.print("The OpenRouter API key is used exclusively for agent orchestration,")
    console.print("NOT for code generation or user-facing text generation.\n")
    
    # Initialize config
    config_root = project_root or Path.cwd()
    config = ConfigManager(config_root)
    
    # Check if API key already exists
    existing_key = config.get_api_key("openrouter")
    if existing_key:
        console.print("[yellow]OpenRouter API key is already configured.[/yellow]")
        if not click.confirm("Do you want to update it?"):
            console.print("Setup cancelled.")
            return
    
    # Prompt for API key
    console.print("\n[bold]Step 1: OpenRouter API Key[/bold]")
    console.print("Get your API key from: [link]https://openrouter.ai/keys[/link]")
    console.print("")
    
    api_key = click.prompt(
        "Enter your OpenRouter API key",
        type=str,
        hide_input=True,
        confirmation_prompt=True,
    )
    
    if not api_key or not api_key.strip():
        console.print("[red]Error: API key cannot be empty[/red]", err=True)
        return
    
    # Ask where to store it
    console.print("\n[bold]Step 2: Storage Location[/bold]")
    console.print("Where would you like to store the API key?")
    console.print("1. Project .env file (recommended)")
    console.print("2. System keyring (secure)")
    
    choice = click.prompt("Choice", type=click.Choice(["1", "2"]), default="1")
    
    try:
        if choice == "1":  # .env file
            config.set_api_key_to_env("openrouter", api_key)
            env_file = config_root / ".env"
            console.print(f"\n[green]✓[/green] API key saved to {env_file}")
            console.print("[dim]Note: Add .env to .gitignore to keep your API key secure[/dim]")
        else:  # keyring
            config.set_api_key("openrouter", api_key)
            console.print("\n[green]✓[/green] API key saved to system keyring")
        
        # Verify the key was saved
        if config.get_api_key("openrouter"):
            console.print("\n[green]✓ Setup completed successfully![/green]")
            console.print("\nYou can now use OmniDev agents in your project.")
        else:
            console.print("\n[yellow]Warning: API key may not be accessible. Please verify.[/yellow]")
            
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]", err=True)
        return


def cli() -> None:
    """Entry point for the CLI."""
    try:
        cli_main.main(standalone_mode=False)
    except OmniDevError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nInterrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()

