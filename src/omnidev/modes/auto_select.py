"""
Auto-Select Mode - Intelligent model routing.

Automatically selects the best AI model for each task
based on task analysis and model capabilities.
"""

from typing import Any

from omnidev.core.exceptions import OmniDevError
from omnidev.modes.base import BaseMode


class AutoSelectMode(BaseMode):
    """Auto-Select Mode - Intelligent model selection."""

    async def execute(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a query with automatic model selection.

        Args:
            query: User query or task description.
            **kwargs: Additional parameters.

        Returns:
            Dictionary with execution results.

        Raises:
            OmniDevError: If execution fails.
        """
        self.logger.info(f"Auto-Select Mode: Executing query: {query}")

        try:
            # Get context
            context = self.get_context(query)
            context_size = len(str(context))

            # Get configured provider and model to respect user's choice
            preferred_provider = self.get_configured_provider()
            preferred_model = self.get_configured_model()

            # Route request (model router handles selection with user's preference)
            response = await self.model_router.route_request(
                query,
                context_size=context_size,
                preferred_model=preferred_model,
                preferred_provider=preferred_provider,
            )

            # Log model usage
            self.session_manager.add_model_usage(
                response.provider,
                response.model,
                response.tokens_used,
                response.cost,
            )

            # Log command
            self.session_manager.add_command(query, "auto", {"model": f"{response.provider}/{response.model}"})

            return {
                "success": True,
                "query": query,
                "response": response.content,
                "model_used": f"{response.provider}/{response.model}",
                "tokens_used": response.tokens_used,
                "cost": response.cost,
                "selection_reason": f"Selected {response.model} based on task analysis",
            }
        except Exception as e:
            self.logger.error(f"Auto-Select Mode execution failed: {e}")
            raise OmniDevError(f"Auto-Select Mode execution failed: {e}") from e

