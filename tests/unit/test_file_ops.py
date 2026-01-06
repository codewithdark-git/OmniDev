"""Unit tests for file operations."""

import tempfile
from pathlib import Path

import pytest

from omnidev.actions.file_ops import FileOperationError, FileOperations
from omnidev.core.exceptions import ValidationError


class TestFileOperations:
    """Test cases for FileOperations."""

    def test_create_file(self) -> None:
        """Test file creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            file_ops = FileOperations(project_root)

            file_path = project_root / "test.txt"
            content = "Hello, World!"

            created = file_ops.create_file(file_path, content)
            assert created.exists()
            assert created.read_text() == content

    def test_read_file(self) -> None:
        """Test file reading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            file_ops = FileOperations(project_root)

            file_path = project_root / "test.txt"
            content = "Test content"
            file_path.write_text(content)

            read_content = file_ops.read_file(file_path)
            assert read_content == content

    def test_update_file(self) -> None:
        """Test file update."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            file_ops = FileOperations(project_root)

            file_path = project_root / "test.txt"
            file_path.write_text("Original")

            updated = file_ops.update_file(file_path, "Updated")
            assert updated.read_text() == "Updated"

    def test_delete_file(self) -> None:
        """Test file deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            file_ops = FileOperations(project_root)

            file_path = project_root / "test.txt"
            file_path.write_text("Test")

            file_ops.delete_file(file_path)
            assert not file_path.exists()

    def test_protected_directory_validation(self) -> None:
        """Test validation of protected directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            file_ops = FileOperations(project_root)

            # Try to create file in protected directory (simulated)
            protected_path = Path("/etc/test.txt")
            with pytest.raises(ValidationError):
                file_ops.create_file(protected_path, "test")

    def test_path_outside_project_validation(self) -> None:
        """Test validation of paths outside project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            file_ops = FileOperations(project_root)

            # Try to access file outside project (use parent directory)
            outside_path = project_root.parent / "outside.txt"
            with pytest.raises(ValidationError):
                file_ops.create_file(outside_path, "test")

