"""
Context builder for assembling project context.

Dynamically selects files, optimizes token usage, and builds
context windows for AI model requests.
"""

from pathlib import Path
from typing import Optional

from omnidev.context.indexer import FileIndexer
from omnidev.context.scorer import RelevanceScorer, RelevanceScore


class ContextBuilder:
    """Builds context for AI model requests."""

    # Rough token estimates (1 token ≈ 4 characters)
    CHARS_PER_TOKEN = 4
    # Reserve tokens for prompt and response
    RESERVED_TOKENS = 2000

    def __init__(
        self,
        indexer: FileIndexer,
        scorer: RelevanceScorer,
        max_tokens: int = 120000,
    ) -> None:
        """Initialize the context builder.

        Args:
            indexer: File indexer instance.
            scorer: Relevance scorer instance.
            max_tokens: Maximum tokens for context window.
        """
        self.indexer = indexer
        self.scorer = scorer
        self.max_tokens = max_tokens
        self.available_tokens = max_tokens - self.RESERVED_TOKENS

    def build_context(
        self,
        query: str,
        explicit_files: Optional[list[Path]] = None,
        max_files: Optional[int] = None,
    ) -> dict[str, str]:
        """Build context dictionary from project files.

        Args:
            query: Query or task description.
            explicit_files: Files explicitly mentioned.
            max_files: Maximum number of files to include.

        Returns:
            Dictionary mapping file paths (as strings) to file contents.
        """
        # Score files for relevance
        max_files = max_files or 50
        scored_files = self.scorer.score_files(query, explicit_files, max_files * 2)

        # Select files within token budget
        selected_files: list[tuple[Path, RelevanceScore]] = []
        tokens_used = 0

        for score in scored_files:
            file_path = score.file_path
            if not file_path.exists():
                continue

            # Estimate tokens for this file
            try:
                content = file_path.read_text(encoding="utf-8")
                file_tokens = len(content) // self.CHARS_PER_TOKEN

                # Check if file fits in budget
                if tokens_used + file_tokens <= self.available_tokens:
                    selected_files.append((file_path, score))
                    tokens_used += file_tokens
                elif len(selected_files) == 0:
                    # If no files selected yet, include at least one (truncated if needed)
                    truncated_content = content[: self.available_tokens * self.CHARS_PER_TOKEN]
                    selected_files.append((file_path, score))
                    tokens_used += len(truncated_content) // self.CHARS_PER_TOKEN
                    break

                # Stop if we've reached max files
                if len(selected_files) >= max_files:
                    break
            except Exception:
                # Skip files that can't be read
                continue

        # Build context dictionary
        context: dict[str, str] = {}
        for file_path, score in selected_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                # Use relative path as key
                rel_path = file_path.relative_to(self.indexer.project_root)
                context[str(rel_path)] = content
            except Exception:
                # Skip files that can't be read
                continue

        return context

    def build_summarized_context(
        self,
        query: str,
        explicit_files: Optional[list[Path]] = None,
        max_files: int = 20,
    ) -> dict[str, str]:
        """Build context with file summaries for low-priority files.

        Args:
            query: Query or task description.
            explicit_files: Files explicitly mentioned.
            max_files: Maximum number of files to include fully.

        Returns:
            Dictionary mapping file paths to contents or summaries.
        """
        # Get scored files
        scored_files = self.scorer.score_files(query, explicit_files, max_files * 3)

        context: dict[str, str] = {}
        tokens_used = 0
        files_included = 0

        for score in scored_files:
            file_path = score.file_path
            if not file_path.exists():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                file_tokens = len(content) // self.CHARS_PER_TOKEN
                rel_path = file_path.relative_to(self.indexer.project_root)

                # Include full content for high-priority files
                if files_included < max_files and tokens_used + file_tokens <= self.available_tokens:
                    context[str(rel_path)] = content
                    tokens_used += file_tokens
                    files_included += 1
                elif score.score > 10.0:
                    # Include summary for medium-priority files
                    summary = self._create_summary(content, file_path)
                    summary_tokens = len(summary) // self.CHARS_PER_TOKEN
                    if tokens_used + summary_tokens <= self.available_tokens:
                        context[str(rel_path)] = summary
                        tokens_used += summary_tokens
                else:
                    # Skip low-priority files
                    break
            except Exception:
                continue

        return context

    def _create_summary(self, content: str, file_path: Path) -> str:
        """Create a summary of file contents.

        Args:
            content: File content.
            file_path: Path to the file.

        Returns:
            Summary string.
        """
        lines = content.split("\n")
        total_lines = len(lines)

        # Extract first few lines (usually imports and docstrings)
        header_lines = min(20, total_lines)
        header = "\n".join(lines[:header_lines])

        # Extract function/class definitions
        definitions: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("def ", "class ", "async def ")):
                definitions.append(stripped)

        # Build summary
        summary_parts = [
            f"# {file_path.name}",
            f"# Total lines: {total_lines}",
            "",
            "# Header:",
            header,
        ]

        if definitions:
            summary_parts.extend([
                "",
                "# Definitions:",
                "\n".join(definitions[:10]),  # Limit to 10 definitions
            ])

        if total_lines > 20:
            summary_parts.extend([
                "",
                f"# ... ({total_lines - 20} more lines)",
            ])

        return "\n".join(summary_parts)

    def estimate_tokens(self, content: str) -> int:
        """Estimate token count for content.

        Args:
            content: Text content.

        Returns:
            Estimated token count.
        """
        return len(content) // self.CHARS_PER_TOKEN

    def get_context_stats(self, context: dict[str, str]) -> dict[str, int]:
        """Get statistics about a context.

        Args:
            context: Context dictionary.

        Returns:
            Dictionary with statistics.
        """
        total_files = len(context)
        total_chars = sum(len(content) for content in context.values())
        total_tokens = total_chars // self.CHARS_PER_TOKEN

        return {
            "files": total_files,
            "characters": total_chars,
            "tokens": total_tokens,
            "tokens_remaining": max(0, self.available_tokens - total_tokens),
        }

