"""
Relevance scoring for file selection in context management.

Scores files based on dependencies, recent edits, naming similarity,
and user focus patterns to determine which files to include in context.
"""

from pathlib import Path
from typing import Optional

from omnidev.context.indexer import FileIndexer, FileMetadata


class RelevanceScore:
    """Represents a relevance score for a file."""

    def __init__(
        self,
        file_path: Path,
        score: float = 0.0,
        reasons: Optional[list[str]] = None,
    ) -> None:
        """Initialize relevance score.

        Args:
            file_path: Path to the file.
            score: Relevance score (higher = more relevant).
            reasons: List of reasons for the score.
        """
        self.file_path = file_path
        self.score = score
        self.reasons = reasons or []

    def __lt__(self, other: "RelevanceScore") -> bool:
        """Compare scores for sorting."""
        return self.score < other.score

    def __repr__(self) -> str:
        """String representation."""
        return f"RelevanceScore({self.file_path.name}, score={self.score:.2f})"


class RelevanceScorer:
    """Scores files for relevance to a given task or context."""

    # Scoring weights
    WEIGHT_DEPENDENCY = 50.0
    WEIGHT_RECENT_EDIT = 30.0
    WEIGHT_NAME_SIMILARITY = 20.0
    WEIGHT_EXPLICIT = 100.0
    WEIGHT_SAME_DIR = 10.0

    def __init__(self, indexer: FileIndexer) -> None:
        """Initialize the relevance scorer.

        Args:
            indexer: File indexer instance.
        """
        self.indexer = indexer
        self.explicit_files: set[Path] = set()
        self.focus_files: set[Path] = set()

    def score_files(
        self,
        query: str,
        explicit_files: Optional[list[Path]] = None,
        max_files: int = 50,
    ) -> list[RelevanceScore]:
        """Score all files for relevance to a query.

        Args:
            query: Query string or task description.
            explicit_files: Files explicitly mentioned by user.
            max_files: Maximum number of files to return.

        Returns:
            List of relevance scores, sorted by score (highest first).
        """
        self.explicit_files = set(explicit_files or [])

        scores: list[RelevanceScore] = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        for file_path, metadata in self.indexer.index.items():
            score = self._calculate_score(file_path, metadata, query_lower, query_words)
            if score.score > 0:
                scores.append(score)

        # Sort by score (descending)
        scores.sort(reverse=True)

        return scores[:max_files]

    def _calculate_score(
        self,
        file_path: Path,
        metadata: FileMetadata,
        query_lower: str,
        query_words: set[str],
    ) -> RelevanceScore:
        """Calculate relevance score for a file.

        Args:
            file_path: Path to the file.
            metadata: File metadata.
            query_lower: Lowercase query string.
            query_words: Set of words in the query.

        Returns:
            RelevanceScore for the file.
        """
        score = 0.0
        reasons: list[str] = []

        # Explicit file mention (highest priority)
        if file_path in self.explicit_files:
            score += self.WEIGHT_EXPLICIT
            reasons.append("explicitly mentioned")

        # Dependency scoring
        dep_score = self._score_dependencies(file_path, metadata)
        if dep_score > 0:
            score += dep_score
            reasons.append("dependency relationship")

        # Recent edit scoring
        recent_score = self._score_recent_edit(metadata)
        if recent_score > 0:
            score += recent_score
            reasons.append("recently modified")

        # Name similarity scoring
        name_score = self._score_name_similarity(file_path, query_lower, query_words)
        if name_score > 0:
            score += name_score
            reasons.append("name similarity")

        # Same directory scoring
        if self.explicit_files:
            for explicit_file in self.explicit_files:
                if file_path.parent == explicit_file.parent:
                    score += self.WEIGHT_SAME_DIR
                    reasons.append("same directory")
                    break

        # Focus file scoring
        if file_path in self.focus_files:
            score += 20.0
            reasons.append("user focus pattern")

        return RelevanceScore(file_path=file_path, score=score, reasons=reasons)

    def _score_dependencies(self, file_path: Path, metadata: FileMetadata) -> float:
        """Score based on dependency relationships.

        Args:
            file_path: Path to the file.
            metadata: File metadata.

        Returns:
            Dependency score.
        """
        if not self.explicit_files:
            return 0.0

        score = 0.0
        dependencies = self.indexer.get_dependencies(file_path)

        # Check if this file is a dependency of explicitly mentioned files
        for explicit_file in self.explicit_files:
            explicit_deps = self.indexer.get_dependencies(explicit_file)
            if file_path in explicit_deps:
                score += self.WEIGHT_DEPENDENCY
                break

        # Check if explicitly mentioned files depend on this file
        for explicit_file in self.explicit_files:
            if explicit_file in dependencies:
                score += self.WEIGHT_DEPENDENCY * 0.5
                break

        return score

    def _score_recent_edit(self, metadata: FileMetadata) -> float:
        """Score based on recent modification time.

        Args:
            metadata: File metadata.

        Returns:
            Recent edit score.
        """
        import time

        current_time = time.time()
        age_seconds = current_time - metadata.last_modified

        # Score decreases with age
        # Files modified in last 24 hours get full score
        # Files modified in last week get partial score
        if age_seconds < 24 * 3600:  # 24 hours
            return self.WEIGHT_RECENT_EDIT
        elif age_seconds < 7 * 24 * 3600:  # 7 days
            return self.WEIGHT_RECENT_EDIT * 0.5
        elif age_seconds < 30 * 24 * 3600:  # 30 days
            return self.WEIGHT_RECENT_EDIT * 0.2
        else:
            return 0.0

    def _score_name_similarity(
        self,
        file_path: Path,
        query_lower: str,
        query_words: set[str],
    ) -> float:
        """Score based on filename similarity to query.

        Args:
            file_path: Path to the file.
            query_lower: Lowercase query string.
            query_words: Set of words in the query.

        Returns:
            Name similarity score.
        """
        file_name_lower = file_path.stem.lower()
        file_words = set(file_name_lower.split("_") + file_name_lower.split("-"))

        # Count matching words
        matches = len(query_words.intersection(file_words))
        if matches == 0:
            return 0.0

        # Score based on number of matches and query length
        match_ratio = matches / len(query_words) if query_words else 0.0
        return self.WEIGHT_NAME_SIMILARITY * match_ratio

    def add_focus_file(self, file_path: Path) -> None:
        """Add a file to focus set (files user frequently works with).

        Args:
            file_path: Path to add to focus set.
        """
        self.focus_files.add(file_path)

    def clear_focus_files(self) -> None:
        """Clear the focus file set."""
        self.focus_files.clear()

