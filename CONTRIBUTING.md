# Contributing to OmniDev

Thank you for your interest in contributing to OmniDev! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up the development environment** (see [README_SETUP.md](README_SETUP.md))
4. **Create a branch** for your changes

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/your-bugfix-name
```

### 2. Make Your Changes

- Follow the guidelines in [AGENTS.md](AGENTS.md)
- Write production-quality code with type hints
- Add docstrings for all public functions/classes
- Write tests for your changes

### 3. Test Your Changes

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=omnidev --cov-report=html

# Run specific test file
pytest tests/unit/test_your_module.py
```

### 4. Format and Lint

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

### 5. Commit Your Changes

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Example**:
```
feat(context): Add automatic file relevance scoring

Implement intelligent file selection based on:
- Import dependencies
- Recent edit history
- User focus patterns

Closes #123
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Standards

### Type Hints

All functions must have type hints:

```python
def process_files(file_paths: list[str], output_dir: Path | None = None) -> dict[str, int]:
    """Process files and return statistics."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def process_files(
    file_paths: list[str],
    output_dir: Path | None = None,
) -> dict[str, int]:
    """Process multiple files and return statistics.
    
    Args:
        file_paths: List of file paths to process
        output_dir: Optional output directory for results
        
    Returns:
        Dictionary with processing statistics
        
    Raises:
        FileNotFoundError: If any file doesn't exist
    """
    pass
```

### Error Handling

Always handle errors properly:

```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise OmniDevError(f"Failed to perform operation: {e}") from e
```

## Testing Guidelines

- Write tests for all new features
- Aim for >80% test coverage
- Test both happy paths and error cases
- Use descriptive test names

## Documentation

- Update relevant documentation when adding features
- Add docstrings to all public APIs
- Update README if needed
- Add examples for new features

## Pull Request Process

1. **Update CHANGELOG.md** with your changes
2. **Ensure all tests pass**
3. **Ensure code is formatted and linted**
4. **Request review** from maintainers
5. **Address review comments**
6. **Wait for approval** before merging

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check [DEVELOPMENT.md](DEVELOPMENT.md) for detailed guidelines
- Read [AGENTS.md](AGENTS.md) for code contribution best practices

Thank you for contributing to OmniDev! 🚀

