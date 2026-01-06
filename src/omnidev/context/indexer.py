"""
File indexer for project context management.

Scans project files, analyzes dependencies, extracts metadata,
and maintains an index for efficient context selection.
"""

import ast
import re
from pathlib import Path
from typing import Any, Optional

from omnidev.core.exceptions import ContextError
from omnidev.core.logger import get_logger


class FileMetadata:
    """Metadata about a project file."""

    def __init__(
        self,
        file_path: Path,
        size: int = 0,
        language: Optional[str] = None,
        imports: list[str] = None,
        exports: list[str] = None,
        last_modified: float = 0.0,
    ) -> None:
        """Initialize file metadata.

        Args:
            file_path: Path to the file.
            size: File size in bytes.
            language: Programming language detected.
            imports: List of imported modules.
            exports: List of exported symbols (functions, classes).
            last_modified: Last modification timestamp.
        """
        self.file_path = file_path
        self.size = size
        self.language = language
        self.imports = imports or []
        self.exports = exports or []
        self.last_modified = last_modified

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "file_path": str(self.file_path),
            "size": self.size,
            "language": self.language,
            "imports": self.imports,
            "exports": self.exports,
            "last_modified": self.last_modified,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileMetadata":
        """Create metadata from dictionary.

        Args:
            data: Dictionary containing metadata.

        Returns:
            FileMetadata instance.
        """
        return cls(
            file_path=Path(data["file_path"]),
            size=data.get("size", 0),
            language=data.get("language"),
            imports=data.get("imports", []),
            exports=data.get("exports", []),
            last_modified=data.get("last_modified", 0.0),
        )


class FileIndexer:
    """Indexes project files for context management."""

    # File extensions by language
    LANGUAGE_EXTENSIONS = {
        "python": {".py", ".pyi"},
        "javascript": {".js", ".jsx"},
        "typescript": {".ts", ".tsx"},
        "java": {".java"},
        "go": {".go"},
        "rust": {".rs"},
        "cpp": {".cpp", ".cc", ".cxx", ".hpp", ".h"},
        "c": {".c", ".h"},
    }

    # Patterns to exclude
    DEFAULT_EXCLUDE_PATTERNS = {
        "__pycache__",
        "*.pyc",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "*.egg-info",
        "dist",
        "build",
        ".omnidev",
    }

    def __init__(self, project_root: Path, exclude_patterns: Optional[set[str]] = None) -> None:
        """Initialize the file indexer.

        Args:
            project_root: Root directory of the project.
            exclude_patterns: Optional additional patterns to exclude.
        """
        self.project_root = project_root.resolve()
        self.logger = get_logger("indexer")
        self.exclude_patterns = self.DEFAULT_EXCLUDE_PATTERNS.copy()
        if exclude_patterns:
            self.exclude_patterns.update(exclude_patterns)
        self.index: dict[Path, FileMetadata] = {}

    def index_project(self) -> dict[Path, FileMetadata]:
        """Index all files in the project.

        Returns:
            Dictionary mapping file paths to metadata.

        Raises:
            ContextError: If indexing fails.
        """
        try:
            self.index.clear()
            self._index_directory(self.project_root)
            self.logger.info(f"Indexed {len(self.index)} files in project")
            return self.index.copy()
        except Exception as e:
            raise ContextError(f"Failed to index project: {e}") from e

    def _index_directory(self, directory: Path) -> None:
        """Recursively index files in a directory.

        Args:
            directory: Directory to index.
        """
        try:
            for item in directory.iterdir():
                if self._should_exclude(item):
                    continue

                if item.is_file():
                    try:
                        metadata = self._extract_metadata(item)
                        if metadata:
                            self.index[item] = metadata
                    except Exception as e:
                        self.logger.debug(f"Failed to index {item}: {e}")
                elif item.is_dir():
                    self._index_directory(item)
        except PermissionError:
            self.logger.warning(f"Permission denied accessing {directory}")

    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded.

        Args:
            path: Path to check.

        Returns:
            True if path should be excluded, False otherwise.
        """
        # Check exact matches
        if path.name in self.exclude_patterns:
            return True

        # Check patterns
        for pattern in self.exclude_patterns:
            if pattern.startswith("*."):
                # Extension pattern
                if path.suffix == pattern[1:]:
                    return True
            elif pattern in str(path):
                # Substring match
                return True

        return False

    def _extract_metadata(self, file_path: Path) -> Optional[FileMetadata]:
        """Extract metadata from a file.

        Args:
            file_path: Path to the file.

        Returns:
            FileMetadata if file is processable, None otherwise.
        """
        try:
            stat = file_path.stat()
            language = self._detect_language(file_path)
            imports: list[str] = []
            exports: list[str] = []

            if language == "python":
                imports, exports = self._parse_python_file(file_path)
            elif language in ("javascript", "typescript"):
                imports, exports = self._parse_js_file(file_path)

            return FileMetadata(
                file_path=file_path,
                size=stat.st_size,
                language=language,
                imports=imports,
                exports=exports,
                last_modified=stat.st_mtime,
            )
        except Exception as e:
            self.logger.debug(f"Failed to extract metadata from {file_path}: {e}")
            return None

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension.

        Args:
            file_path: Path to the file.

        Returns:
            Language name if detected, None otherwise.
        """
        suffix = file_path.suffix.lower()
        for language, extensions in self.LANGUAGE_EXTENSIONS.items():
            if suffix in extensions:
                return language
        return None

    def _parse_python_file(self, file_path: Path) -> tuple[list[str], list[str]]:
        """Parse Python file for imports and exports.

        Args:
            file_path: Path to Python file.

        Returns:
            Tuple of (imports, exports) lists.
        """
        imports: list[str] = []
        exports: list[str] = []

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))

            for node in ast.walk(tree):
                # Collect imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)

                # Collect exports (functions and classes at module level)
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    if node.name and not node.name.startswith("_"):
                        exports.append(node.name)
        except Exception:
            # If parsing fails, return empty lists
            pass

        return imports, exports

    def _parse_js_file(self, file_path: Path) -> tuple[list[str], list[str]]:
        """Parse JavaScript/TypeScript file for imports and exports.

        Args:
            file_path: Path to JS/TS file.

        Returns:
            Tuple of (imports, exports) lists.
        """
        imports: list[str] = []
        exports: list[str] = []

        try:
            content = file_path.read_text(encoding="utf-8")

            # Match import statements
            import_pattern = r"import\s+(?:(?:\*\s+as\s+\w+)|(?:\{[^}]*\})|(?:\w+))\s+from\s+['\"]([^'\"]+)['\"]"
            for match in re.finditer(import_pattern, content):
                imports.append(match.group(1))

            # Match require statements
            require_pattern = r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
            for match in re.finditer(require_pattern, content):
                imports.append(match.group(1))

            # Match export statements (simplified)
            export_pattern = r"export\s+(?:function|class|const|let|var)\s+(\w+)"
            for match in re.finditer(export_pattern, content):
                exports.append(match.group(1))
        except Exception:
            # If parsing fails, return empty lists
            pass

        return imports, exports

    def get_file_metadata(self, file_path: Path) -> Optional[FileMetadata]:
        """Get metadata for a specific file.

        Args:
            file_path: Path to the file.

        Returns:
            FileMetadata if found, None otherwise.
        """
        return self.index.get(file_path)

    def get_dependencies(self, file_path: Path) -> list[Path]:
        """Get files that a file depends on (via imports).

        Args:
            file_path: Path to the file.

        Returns:
            List of dependent file paths.
        """
        metadata = self.get_file_metadata(file_path)
        if not metadata or not metadata.imports:
            return []

        dependencies: list[Path] = []
        for import_name in metadata.imports:
            dep_path = self._resolve_import(import_name, file_path)
            if dep_path and dep_path in self.index:
                dependencies.append(dep_path)

        return dependencies

    def _resolve_import(self, import_name: str, from_file: Path) -> Optional[Path]:
        """Resolve an import name to a file path.

        Args:
            import_name: Import module name.
            from_file: File that contains the import.

        Returns:
            Resolved file path if found, None otherwise.
        """
        # Remove relative import markers
        import_name = import_name.replace(".", "/")

        # Try different resolutions
        candidates = [
            self.project_root / import_name,
            self.project_root / f"{import_name}.py",
            from_file.parent / import_name,
            from_file.parent / f"{import_name}.py",
        ]

        for candidate in candidates:
            if candidate.exists() and candidate in self.index:
                return candidate

        return None

    def update_file(self, file_path: Path) -> None:
        """Update metadata for a single file.

        Args:
            file_path: Path to the file to update.
        """
        if file_path.exists() and not self._should_exclude(file_path):
            metadata = self._extract_metadata(file_path)
            if metadata:
                self.index[file_path] = metadata

