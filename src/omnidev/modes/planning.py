"""
Planning Mode - Strategic planning before execution.

Analyzes requirements, creates detailed plans, shows impact,
and waits for user approval before executing.
"""

from pathlib import Path
from typing import Any, Optional

from omnidev.core.exceptions import OmniDevError
from omnidev.modes.base import BaseMode
from omnidev.prompts.loader import PromptLoader


class PlanningMode(BaseMode):
    """Planning Mode - Think before acting."""

    async def execute(self, query: str, auto_approve: bool = False, **kwargs: Any) -> dict[str, Any]:
        """Execute a query with planning.

        Args:
            query: User query or task description.
            auto_approve: Whether to auto-approve plan (for testing).
            **kwargs: Additional parameters.

        Returns:
            Dictionary with planning and execution results.

        Raises:
            OmniDevError: If execution fails.
        """
        self.logger.info(f"Planning Mode: Planning for query: {query}")

        try:
            # Load planning mode template
            try:
                prompt_loader = PromptLoader()
                mode_template = prompt_loader.load("templates", "planning_mode")
                # Include mode template in context for planning
                query_with_mode = f"{mode_template}\n\n## Task to Plan\n{query}"
            except Exception as e:
                self.logger.warning(f"Failed to load planning mode template: {e}")
                query_with_mode = query
            
            # Get context
            context = self.get_context(query)

            # Generate plan using mode-aware query
            plan = await self._generate_plan(query_with_mode, context)

            # If auto_approve, execute immediately
            if auto_approve:
                execution_results = await self._execute_plan(plan)
                return {
                    "success": True,
                    "query": query,
                    "plan": plan,
                    "execution": execution_results,
                }

            # Return plan for user approval
            return {
                "success": True,
                "query": query,
                "plan": plan,
                "approved": False,
                "message": "Plan generated. Awaiting user approval.",
            }
        except Exception as e:
            self.logger.error(f"Planning Mode execution failed: {e}")
            raise OmniDevError(f"Planning Mode execution failed: {e}") from e

    async def _generate_plan(self, query: str, context: dict[str, str]) -> dict[str, Any]:
        """Generate an execution plan.

        Args:
            query: User query.
            context: Project context.

        Returns:
            Plan dictionary with phases and steps.
        """
        # Route to model for planning using configured provider
        planning_query = f"Create a detailed implementation plan for: {query}\n\nConsider the project context and break down into phases with estimated effort."
        preferred_provider = self.get_configured_provider()
        preferred_model = self.get_configured_model()
        response = await self.model_router.route_request(
            planning_query, 
            context_size=len(str(context)),
            preferred_model=preferred_model,
            preferred_provider=preferred_provider,
        )

        # Parse plan from response (simplified - full implementation would parse structured plan)
        plan = {
            "phases": [
                {
                    "name": "Analysis",
                    "description": "Analyze requirements and current codebase",
                    "estimated_time": "5-10 minutes",
                    "files_affected": [],
                },
                {
                    "name": "Implementation",
                    "description": "Implement the requested changes",
                    "estimated_time": "15-30 minutes",
                    "files_affected": [],
                },
                {
                    "name": "Testing",
                    "description": "Generate and run tests",
                    "estimated_time": "5-10 minutes",
                    "files_affected": [],
                },
            ],
            "total_estimated_time": "25-50 minutes",
            "risk_level": "medium",
            "breaking_changes": False,
            "ai_plan": response.content,
        }

        return plan

    async def _execute_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Execute an approved plan.

        Args:
            plan: Plan dictionary.

        Returns:
            Execution results.
        """
        results = {
            "phases_completed": [],
            "files_created": [],
            "files_modified": [],
            "errors": [],
        }

        # Execute each phase
        for phase in plan.get("phases", []):
            try:
                self.logger.info(f"Executing phase: {phase['name']}")
                # In full implementation, would execute phase steps
                results["phases_completed"].append(phase["name"])
            except Exception as e:
                results["errors"].append(f"Phase {phase['name']}: {e}")

        return results

    async def approve_and_execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Approve and execute a plan.

        Args:
            plan: Plan dictionary.

        Returns:
            Execution results.
        """
        return await self._execute_plan(plan)

