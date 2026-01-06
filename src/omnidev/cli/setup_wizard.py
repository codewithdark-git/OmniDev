"""
Interactive setup wizard for OmniDev.

Guides users through provider, model, and mode selection.
"""

from pathlib import Path
from typing import Any, Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from omnidev.context.indexer import FileIndexer
from omnidev.core.config import ConfigManager
from omnidev.core.logger import get_logger
from omnidev.models.registry import ProviderRegistry

console = Console()
logger = get_logger("setup_wizard")


class SetupWizard:
    """Interactive setup wizard for OmniDev configuration."""

    # Available providers (user-selectable)
    # Note: G4F is hidden until stability issues are resolved
    PROVIDERS = {
        "groq": {
            "name": "Groq (Free)",
            "description": "Fast inference with free tier (30 req/min limit)",
            "requires_api_key": True,
        },
        "openai": {
            "name": "OpenAI API",
            "description": "Official OpenAI API (requires API key)",
            "requires_api_key": True,
        },
        "anthropic": {
            "name": "Anthropic API",
            "description": "Official Anthropic/Claude API (requires API key)",
            "requires_api_key": True,
        },
        "google": {
            "name": "Google API",
            "description": "Official Google/Gemini API (requires API key)",
            "requires_api_key": True,
        },
        "openrouter": {
            "name": "OpenRouter",
            "description": "OpenRouter API for multiple models (requires API key)",
            "requires_api_key": True,
        },
    }

    # Available modes
    MODES = {
        "auto": {
            "name": "Auto-Select Mode",
            "description": "Intelligently selects the best model for each task",
        },
        "agent": {
            "name": "Agent Mode",
            "description": "Full autonomy - handles everything automatically",
        },
        "planning": {
            "name": "Planning Mode",
            "description": "Shows plan first, then executes with approval",
        },
        "manual": {
            "name": "Manual Mode",
            "description": "Full control - you approve every step",
        },
    }

    def __init__(self, config: ConfigManager, project_root: Path) -> None:
        """Initialize setup wizard.

        Args:
            config: ConfigManager instance.
            project_root: Project root directory.
        """
        self.config = config
        self.project_root = project_root
        self.provider_registry = ProviderRegistry(config, auto_register=False)

    def run(self) -> dict[str, Any]:
        """Run the setup wizard.

        Returns:
            Dictionary with selected provider, model, and mode.
        """
        console.print("\n[bold cyan]OmniDev Setup Wizard[/bold cyan]")
        console.print("=" * 60)

        # Step 1: Index files
        files_indexed = self._index_files()

        # Step 2: Select provider
        provider = self._select_provider()

        # Step 3: Select model
        model = self._select_model(provider)

        # Step 4: Select mode
        mode = self._select_mode()

        # Step 5: Save configuration
        self._save_configuration(provider, model, mode)

        console.print("\n[green]✓ Setup completed successfully![/green]")
        console.print(f"\n[dim]Files indexed: {files_indexed}[/dim]")
        console.print(f"[dim]Provider: {provider}[/dim]")
        console.print(f"[dim]Model: {model}[/dim]")
        console.print(f"[dim]Mode: {mode}[/dim]\n")

        return {
            "provider": provider,
            "model": model,
            "mode": mode,
            "files_indexed": files_indexed,
        }

    def _index_files(self) -> int:
        """Index project files with progress display.

        Returns:
            Number of files indexed.
        """
        console.print("\n[bold]Step 1: Indexing Project Files[/bold]")
        console.print("Scanning project structure...\n")

        try:
            indexer = FileIndexer(self.project_root)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Indexing files...", total=None)
                
                index = indexer.index_project()
                progress.update(task, completed=True)

            files_count = len(index)
            console.print(f"[green]✓[/green] Indexed {files_count} files")
            return files_count
        except Exception as e:
            logger.warning(f"File indexing had issues: {e}")
            console.print(f"[yellow]⚠[/yellow] File indexing had issues: {e}")
            return 0

    def _select_provider(self) -> str:
        """Select AI provider.

        Returns:
            Selected provider name.
        """
        console.print("\n[bold]Step 2: Select AI Provider[/bold]")
        console.print("Choose which provider you want to use for code generation:\n")

        # Show available providers
        provider_options = []
        for idx, (key, info) in enumerate(self.PROVIDERS.items(), 1):
            api_key_status = ""
            if info["requires_api_key"]:
                api_key = self.config.get_api_key(key)
                if api_key:
                    api_key_status = " [green](API key configured)[/green]"
                else:
                    api_key_status = " [yellow](API key needed)[/yellow]"
            
            console.print(f"  {idx}. {info['name']}{api_key_status}")
            console.print(f"     {info['description']}\n")
            provider_options.append(key)

        # Get user selection
        while True:
            try:
                choice = click.prompt(
                    "Select provider (1-5)",
                    type=click.IntRange(1, len(provider_options)),
                    default=1,
                )
                selected_provider = provider_options[choice - 1]
                
                # Check if API key is needed
                provider_info = self.PROVIDERS[selected_provider]
                if provider_info["requires_api_key"]:
                    api_key = self.config.get_api_key(selected_provider)
                    if not api_key:
                        console.print(f"\n[yellow]⚠[/yellow] {provider_info['name']} requires an API key.")
                        if click.confirm("Do you want to configure it now?"):
                            api_key = click.prompt(
                                f"Enter your {provider_info['name']} API key",
                                type=str,
                                hide_input=True,
                            )
                            if api_key:
                                self.config.set_api_key(selected_provider, api_key)
                                console.print("[green]✓[/green] API key saved")
                            else:
                                console.print("[red]API key cannot be empty[/red]")
                                continue
                        else:
                            console.print("[yellow]Skipping API key configuration. You can set it later with:[/yellow]")
                            console.print(f"[dim]omnidev config add-key {selected_provider} YOUR_API_KEY[/dim]\n")
                            if not click.confirm("Continue without API key?"):
                                continue
                
                # Register provider with priority 0 (highest) since it's being selected as primary
                if selected_provider == "groq":
                    api_key = self.config.get_api_key("groq")
                    if api_key:
                        from omnidev.models.providers.groq import GroqProvider
                        self.provider_registry.register_provider_lazy(
                            "groq",
                            lambda: GroqProvider(api_key=api_key),
                            priority=0,
                        )
                elif selected_provider == "openai":
                    api_key = self.config.get_api_key("openai")
                    if api_key:
                        from omnidev.models.providers.openai import OpenAIProvider
                        self.provider_registry.register_provider_lazy(
                            "openai",
                            lambda: OpenAIProvider(api_key=api_key),
                            priority=0,  # Primary provider gets highest priority
                        )
                elif selected_provider == "anthropic":
                    api_key = self.config.get_api_key("anthropic")
                    if api_key:
                        from omnidev.models.providers.anthropic import AnthropicProvider
                        self.provider_registry.register_provider_lazy(
                            "anthropic",
                            lambda: AnthropicProvider(api_key=api_key),
                            priority=0,
                        )
                elif selected_provider == "google":
                    api_key = self.config.get_api_key("google")
                    if api_key:
                        from omnidev.models.providers.google import GoogleProvider
                        self.provider_registry.register_provider_lazy(
                            "google",
                            lambda: GoogleProvider(api_key=api_key),
                            priority=0,
                        )
                elif selected_provider == "openrouter":
                    api_key = self.config.get_api_key("openrouter")
                    if api_key:
                        from omnidev.models.providers.openrouter import OpenRouterProvider
                        self.provider_registry.register_provider_lazy(
                            "openrouter",
                            lambda: OpenRouterProvider(api_key=api_key),
                            priority=0,
                        )
                
                return selected_provider
            except (ValueError, click.Abort):
                console.print("[red]Invalid selection. Please try again.[/red]\n")
                continue

    def _select_model(self, provider: str) -> str:
        """Select model from provider.

        Args:
            provider: Selected provider name.

        Returns:
            Selected model name.
        """
        console.print(f"\n[bold]Step 3: Select Model from {self.PROVIDERS[provider]['name']}[/bold]")

        # Get available models for provider
        models = self._get_provider_models(provider)
        
        if not models:
            console.print(f"[yellow]⚠[/yellow] No models available for {provider}")
            console.print("[yellow]Using default model selection[/yellow]")
            return "auto"

        console.print(f"\nAvailable models:\n")
        for idx, model in enumerate(models, 1):
            console.print(f"  {idx}. {model}")

        # Get user selection
        while True:
            try:
                choice = click.prompt(
                    f"Select model (1-{len(models)})",
                    type=click.IntRange(1, len(models)),
                    default=1,
                )
                selected_model = models[choice - 1]
                console.print(f"[green]✓[/green] Selected: {selected_model}")
                return selected_model
            except (ValueError, click.Abort):
                console.print("[red]Invalid selection. Please try again.[/red]\n")
                continue

    def _get_provider_models(self, provider: str) -> list[str]:
        """Get available models for a provider.

        Args:
            provider: Provider name.

        Returns:
            List of available model names.
        """
        if provider == "groq":
            return [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
                "gemma2-9b-it",
            ]
        elif provider == "openai":
            return ["gpt-4o", "gpt-4-turbo", "gpt-4o-mini", "gpt-3.5-turbo"]
        elif provider == "anthropic":
            return ["claude-sonnet-4", "claude-opus-4", "claude-haiku-4"]
        elif provider == "google":
            return ["gemini-2.0-flash", "gemini-2.5-pro", "gemini-pro"]
        elif provider == "openrouter":
            # OpenRouter has many models, show common ones
            return [
                "openai/gpt-4o",
                "anthropic/claude-sonnet-4",
                "google/gemini-2.0-flash",
                "mistralai/mistral-large",
            ]
        else:
            return []

    def _select_mode(self) -> str:
        """Select operational mode.

        Returns:
            Selected mode name.
        """
        console.print("\n[bold]Step 4: Select Operational Mode[/bold]")
        console.print("Choose how OmniDev should operate:\n")

        # Show available modes
        mode_options = []
        for idx, (key, info) in enumerate(self.MODES.items(), 1):
            console.print(f"  {idx}. {info['name']}")
            console.print(f"     {info['description']}\n")
            mode_options.append(key)

        # Get user selection
        while True:
            try:
                choice = click.prompt(
                    "Select mode (1-4)",
                    type=click.IntRange(1, len(mode_options)),
                    default=1,
                )
                selected_mode = mode_options[choice - 1]
                console.print(f"[green]✓[/green] Selected: {self.MODES[selected_mode]['name']}")
                return selected_mode
            except (ValueError, click.Abort):
                console.print("[red]Invalid selection. Please try again.[/red]\n")
                continue

    def _save_configuration(self, provider: str, model: str, mode: str) -> None:
        """Save configuration to project config.

        Args:
            provider: Selected provider.
            model: Selected model.
            mode: Selected mode.
        """
        console.print("\n[bold]Step 5: Saving Configuration[/bold]")

        try:
            config = self.config.get_config()
            
            # Update model config
            config.models.preferred = model
            config.models.fallback = provider
            
            # Update mode config
            config.mode.default_mode = mode
            
            # Save configuration (pass the updated config)
            self.config.save_project_config(config)
            
            console.print("[green]✓[/green] Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            console.print(f"[red]✗[/red] Failed to save configuration: {e}")

