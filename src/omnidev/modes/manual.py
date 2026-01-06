"""
Manual Mode - Full user control.

User explicitly controls every decision, selects models,
and approves each action step-by-step.
"""

from typing import Any, Optional

from omnidev.core.exceptions import OmniDevError
from omnidev.modes.base import BaseMode


class ManualMode(BaseMode):
    """Manual Mode - Full user control."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize Manual Mode."""
        super().__init__(*args, **kwargs)
        self.pending_actions: list[dict[str, Any]] = []

    async def execute(
        self,
        query: str,
        user_choices: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute a query with manual control.

        Args:
            query: User query or task description.
            user_choices: Dictionary with user's choices (model, actions, etc.).
            **kwargs: Additional parameters.

        Returns:
            Dictionary with execution results and next steps.

        Raises:
            OmniDevError: If execution fails.
        """
        self.logger.info(f"Manual Mode: Processing query: {query}")

        try:
            # If user has made choices, execute them
            if user_choices:
                return await self._execute_user_choices(query, user_choices)

            # Otherwise, present options to user
            return await self._present_options(query)
        except Exception as e:
            self.logger.error(f"Manual Mode execution failed: {e}")
            raise OmniDevError(f"Manual Mode execution failed: {e}") from e

    async def _present_options(self, query: str) -> dict[str, Any]:
        """Present options to user.

        Args:
            query: User query.

        Returns:
            Dictionary with options for user.
        """
        # Get available models
        available_models = []
        for provider_name in self.model_router.registry.list_providers():
            provider = self.model_router.registry.get_provider(provider_name)
            if provider:
                for model in provider.list_models():
                    available_models.append(f"{provider_name}/{model}")

        return {
            "success": True,
            "query": query,
            "options": {
                "models": available_models,
                "actions": ["generate", "explain", "refactor", "test"],
            },
            "message": "Please select a model and action type",
            "requires_user_input": True,
        }

    async def _execute_user_choices(self, query: str, choices: dict[str, Any]) -> dict[str, Any]:
        """Execute based on user choices.

        Args:
            query: User query.
            choices: User's choices.

        Returns:
            Execution results.
        """
        # Extract choices
        model_str = choices.get("model", "").split("/")
        provider_name = model_str[0] if len(model_str) > 0 else None
        model_name = model_str[1] if len(model_str) > 1 else None

        # Get context
        context = self.get_context(query)

        # Route to selected model
        response = await self.model_router.route_request(
            query,
            context_size=len(str(context)),
            preferred_model=model_name,
            preferred_provider=provider_name,
        )

        # Log usage
        self.session_manager.add_model_usage(
            response.provider,
            response.model,
            response.tokens_used,
            response.cost,
        )

        # Log command
        self.session_manager.add_command(query, "manual", {"model": f"{response.provider}/{response.model}"})

        return {
            "success": True,
            "query": query,
            "response": response.content,
            "model_used": f"{response.provider}/{response.model}",
            "user_choices": choices,
        }

