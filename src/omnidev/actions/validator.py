"""
Code validation for OmniDev.

Provides syntax checking, import validation, and pre-write validation
to ensure code quality before applying changes.
"""

import ast
import importlib.util
from pathlib import Path
from typing import Optional

from omnidev.core.exceptions import ValidationError
from omnidev.core.logger import get_logger


class CodeValidator:
    """Validates code before writing to files."""

    def __init__(self, project_root: Path) -> None:
        """Initialize the code validator.

        Args:
            project_root: Root directory of the project.
        """
        self.project_root = project_root.resolve()
        self.logger = get_logger("validator")

    def validate_python(self, content: str, file_path: Optional[Path] = None) -> bool:
        """Validate Python code syntax.

        Args:
            content: Python code content.
            file_path: Optional file path for error reporting.

        Returns:
            True if valid, False otherwise.

        Raises:
            ValidationError: If code has syntax errors.
        """
        try:
            ast.parse(content, filename=str(file_path) if file_path else "<string>")
            return True
        except SyntaxError as e:
            error_msg = f"Python syntax error: {e.msg} at line {e.lineno}"
            if file_path:
                error_msg += f" in {file_path}"
            raise ValidationError(error_msg) from e
        except Exception as e:
            raise ValidationError(f"Failed to validate Python code: {e}") from e

    def validate_imports(self, content: str, file_path: Optional[Path] = None) -> list[str]:
        """Validate that imports can be resolved.

        Args:
            content: Code content to check.
            file_path: Optional file path for context.

        Returns:
            List of unresolved import names.

        Raises:
            ValidationError: If code cannot be parsed.
        """
        try:
            tree = ast.parse(content, filename=str(file_path) if file_path else "<string>")
            unresolved: list[str] = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._can_import(alias.name):
                            unresolved.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and not self._can_import(node.module):
                        unresolved.append(node.module)

            return unresolved
        except SyntaxError as e:
            raise ValidationError(f"Cannot validate imports - syntax error: {e}") from e
        except Exception as e:
            raise ValidationError(f"Failed to validate imports: {e}") from e

    def _can_import(self, module_name: str) -> bool:
        """Check if a module can be imported.

        Args:
            module_name: Module name to check.

        Returns:
            True if module can be imported, False otherwise.
        """
        try:
            # Try to find the module
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ImportError, ValueError, ModuleNotFoundError):
            # Also check if it's a local file
            module_path = self.project_root / module_name.replace(".", "/")
            if module_path.exists() or (module_path.with_suffix(".py")).exists():
                return True
            return False

    def validate_file(self, file_path: Path, content: Optional[str] = None) -> bool:
        """Validate a file based on its extension.

        Args:
            file_path: Path to the file.
            content: Optional content. If None, reads from file.

        Returns:
            True if valid, False otherwise.

        Raises:
            ValidationError: If validation fails.
        """
        if content is None:
            if not file_path.exists():
                raise ValidationError(f"File does not exist: {file_path}")
            content = file_path.read_text(encoding="utf-8")

        # Validate based on file extension
        suffix = file_path.suffix.lower()

        if suffix == ".py":
            return self.validate_python(content, file_path)
        elif suffix in (".js", ".jsx", ".ts", ".tsx"):
            # JavaScript/TypeScript validation would go here
            # For now, just check basic syntax
            return self._validate_js_basic(content)
        else:
            # For other file types, just check that content is not empty
            return len(content.strip()) > 0

    def _validate_js_basic(self, content: str) -> bool:
        """Basic JavaScript/TypeScript validation.

        Args:
            content: Code content.

        Returns:
            True if passes basic checks, False otherwise.
        """
        # Basic checks: balanced braces, parentheses, brackets
        stack: list[str] = []
        pairs = {"(": ")", "[": "]", "{": "}"}

        for char in content:
            if char in pairs:
                stack.append(char)
            elif char in pairs.values():
                if not stack or pairs[stack.pop()] != char:
                    raise ValidationError("Unbalanced brackets, braces, or parentheses")
        if stack:
            raise ValidationError("Unbalanced brackets, braces, or parentheses")

        return True

    def pre_write_validation(self, file_path: Path, content: str) -> bool:
        """Validate content before writing to file.

        Args:
            file_path: Destination file path.
            content: Content to write.

        Returns:
            True if validation passes.

        Raises:
            ValidationError: If validation fails.
        """
        # Check content is not empty
        if not content.strip():
            raise ValidationError("Content cannot be empty")

        # Validate based on file type
        return self.validate_file(file_path, content)

