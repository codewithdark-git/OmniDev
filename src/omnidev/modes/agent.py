"""
Agent Mode - Full autonomy mode.

Executes tasks autonomously with minimal human intervention,
only asking for confirmation on destructive operations.
"""

import re
from pathlib import Path
from typing import Any, Optional

from omnidev.core.exceptions import OmniDevError
from omnidev.modes.base import BaseMode
from omnidev.prompts.loader import PromptLoader


class AgentMode(BaseMode):
    """Agent Mode - Full autonomous execution."""

    async def execute(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a query autonomously.

        Args:
            query: User query or task description.
            **kwargs: Additional parameters (not used in agent mode).

        Returns:
            Dictionary with execution results.

        Raises:
            OmniDevError: If execution fails.
        """
        self.logger.info(f"Agent Mode: Executing query: {query}")
        
        # Load agent mode template
        try:
            prompt_loader = PromptLoader()
            mode_template = prompt_loader.load("templates", "agent_mode")
            # Include mode template in context for the model
            query_with_mode = f"{mode_template}\n\n## Task\n{query}"
        except Exception as e:
            self.logger.warning(f"Failed to load agent mode template: {e}")
            query_with_mode = query

        try:
            # Get context
            context = self.get_context(query)

            # Get configured provider and model
            preferred_provider = self.get_configured_provider()
            preferred_model = self.get_configured_model()

            # Route to model with mode-aware query using configured provider
            response = await self.model_router.route_request(
                query_with_mode, 
                context_size=len(str(context)),
                preferred_model=preferred_model,
                preferred_provider=preferred_provider,
            )

            # Parse response for file operations
            operations = self._parse_response(response.content, query)

            # Execute operations
            results = await self._execute_operations(operations, query)

            # Log command
            self.session_manager.add_command(query, "agent", results)

            return {
                "success": True,
                "query": query,
                "response": response.content,
                "operations": results,
                "model_used": f"{response.provider}/{response.model}",
            }
        except Exception as e:
            self.logger.error(f"Agent Mode execution failed: {e}")
            raise OmniDevError(f"Agent Mode execution failed: {e}") from e

    def _parse_response(self, content: str, query: str) -> list[dict[str, Any]]:
        """Parse AI response to extract file operations.

        Args:
            content: AI response content.
            query: Original query.

        Returns:
            List of operation dictionaries.
        """
        operations: list[dict[str, Any]] = []

        # Look for file creation patterns
        create_pattern = r"(?:create|add|make|write)\s+(?:file\s+)?([^\s]+\.\w+)"
        for match in re.finditer(create_pattern, content, re.IGNORECASE):
            file_path = match.group(1)
            operations.append({"type": "create", "path": file_path})

        # Look for file modification patterns
        modify_pattern = r"(?:modify|update|edit|change)\s+(?:file\s+)?([^\s]+\.\w+)"
        for match in re.finditer(modify_pattern, content, re.IGNORECASE):
            file_path = match.group(1)
            operations.append({"type": "modify", "path": file_path})

        # If no operations found, try to infer from query
        if not operations:
            if any(word in query.lower() for word in ["create", "add", "make", "write", "new"]):
                # Try to extract filename from query
                filename_match = re.search(r"([a-zA-Z_][a-zA-Z0-9_]*\.(py|js|ts|jsx|tsx|md|txt))", query)
                if filename_match:
                    operations.append({"type": "create", "path": filename_match.group(1)})

        return operations

    async def _execute_operations(self, operations: list[dict[str, Any]], query: str) -> dict[str, Any]:
        """Execute parsed operations.

        Args:
            operations: List of operations to execute.
            query: Original query for context.

        Returns:
            Dictionary with operation results.
        """
        results = {
            "files_created": [],
            "files_modified": [],
            "files_deleted": [],
            "errors": [],
        }

        for operation in operations:
            op_type = operation.get("type")
            file_path_str = operation.get("path")

            if not file_path_str:
                continue

            try:
                file_path = Path(file_path_str)
                if not file_path.is_absolute():
                    file_path = self.project_root / file_path

                if op_type == "create":
                    # For now, create empty file (in full implementation, would generate content)
                    content = f"# Generated by OmniDev\n# Query: {query}\n\n"
                    created = self.create_file_safe(file_path, content)
                    results["files_created"].append(str(created))
                elif op_type == "modify":
                    # Read existing content and modify (simplified)
                    if file_path.exists():
                        existing = self.file_ops.read_file(file_path)
                        # In full implementation, would use AI to modify content
                        updated = self.update_file_safe(file_path, existing)
                        results["files_modified"].append(str(updated))
            except Exception as e:
                results["errors"].append(f"{op_type} {file_path_str}: {e}")

        return results

