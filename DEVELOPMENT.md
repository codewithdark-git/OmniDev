# OmniDev - Development Guide

This guide provides instructions for setting up, developing, and contributing to OmniDev.

---

## Table of Contents

1. [Setup Instructions](#setup-instructions)
2. [Code Standards](#code-standards)
3. [Architecture Decisions](#architecture-decisions)
4. [Adding New Features](#adding-new-features)
5. [Testing Guidelines](#testing-guidelines)
6. [Documentation Standards](#documentation-standards)
7. [Git Workflow](#git-workflow)
8. [Release Process](#release-process)

---

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- Git
- Virtual environment tool (venv, virtualenv, or poetry)

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/omnidev.git
   cd omnidev
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Install in development mode**:
   ```bash
   pip install -e .
   ```

5. **Configure OpenRouter API key** (required for agents):
   ```bash
   omnidev setup
   ```
   Or create a `.env` file:
   ```bash
   echo "OMNIDEV_OPENROUTER_API_KEY=your-key-here" > .env
   ```

6. **Verify installation**:
   ```bash
   omnidev --version
   omnidev config list-keys  # Verify OpenRouter key is configured
   ```

### Development Dependencies

- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities
- **pytest-cov**: Coverage reporting
- **black**: Code formatting
- **ruff**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks

### IDE Setup

**VS Code**:
- Install Python extension
- Install Pylance
- Configure `.vscode/settings.json`:
  ```json
  {
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.testing.pytestEnabled": true
  }
  ```

**PyCharm**:
- Configure Python interpreter
- Enable pytest as test runner
- Install black and ruff plugins

---

## Code Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

1. **Line Length**: 100 characters (not 79)
2. **Type Hints**: Required for all function signatures
3. **Docstrings**: Google style for all public functions/classes
4. **Imports**: Organized with isort (stdlib, third-party, local)

### Code Formatting

**Black** is used for automatic formatting:
```bash
black src/ tests/
```

**Ruff** is used for linting:
```bash
ruff check src/ tests/
ruff format src/ tests/  # Also formats with black
```

### Type Checking

**mypy** is used for static type checking:
```bash
mypy src/
```

Type hints are required for:
- Function parameters and return types
- Class attributes
- Module-level variables (when appropriate)

### Example Code Style

```python
from typing import Optional, List
from pathlib import Path

def process_files(
    file_paths: List[Path],
    output_dir: Optional[Path] = None,
) -> dict[str, int]:
    """
    Process multiple files and return statistics.
    
    Args:
        file_paths: List of file paths to process
        output_dir: Optional output directory for results
        
    Returns:
        Dictionary with processing statistics
        
    Raises:
        FileNotFoundError: If any file doesn't exist
        PermissionError: If output_dir is not writable
    """
    if output_dir is None:
        output_dir = Path.cwd() / "output"
    
    stats = {"processed": 0, "errors": 0}
    # ... implementation ...
    return stats
```

### Naming Conventions

- **Functions/Methods**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Prefix with `_` (single underscore)
- **Protected**: Prefix with `__` (double underscore, rarely used)

---

## Architecture Decisions

### Key Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Dependency Injection**: Dependencies passed as parameters
3. **Interface Segregation**: Small, focused interfaces
4. **Open/Closed**: Open for extension, closed for modification
5. **Testability**: All components easily testable

### Module Structure

```
src/omnidev/
├── cli/              # CLI interface (user interaction)
├── core/             # Core orchestration (business logic)
├── modes/            # Operational modes (Agent, Planning, etc.)
├── models/           # AI provider abstraction
├── context/          # Context management
├── actions/          # File operations and execution
├── tools/            # Extended tools (web search, docs, etc.)
└── utils/            # Shared utilities
```

### Design Patterns Used

1. **Adapter Pattern**: Provider abstraction layer
2. **Strategy Pattern**: Different modes of operation
3. **Factory Pattern**: Model/provider creation
4. **Observer Pattern**: Context updates
5. **Command Pattern**: Action execution

### Error Handling

- Use custom exception classes
- Provide clear error messages
- Log errors appropriately
- Never silently fail
- Always provide recovery options

**Example**:
```python
class OmniDevError(Exception):
    """Base exception for OmniDev errors."""
    pass

class ProviderError(OmniDevError):
    """Error related to AI provider."""
    pass

class FileOperationError(OmniDevError):
    """Error during file operations."""
    pass
```

---

## Adding New Features

### Feature Development Process

1. **Create Issue**: Document the feature request
2. **Design**: Discuss architecture and approach
3. **Create Branch**: `feature/feature-name`
4. **Implement**: Write code with tests
5. **Test**: Ensure all tests pass
6. **Document**: Update documentation
7. **Review**: Submit PR for review
8. **Merge**: After approval

### Feature Checklist

- [ ] Feature implemented
- [ ] Unit tests written
- [ ] Integration tests written (if applicable)
- [ ] Documentation updated
- [ ] Type hints added
- [ ] Code formatted (black, ruff)
- [ ] Type checked (mypy)
- [ ] All tests passing
- [ ] No new linting errors
- [ ] PR description complete

### Adding a New AI Provider

1. **Create Provider Class**:
   ```python
   # src/omnidev/models/providers/new_provider.py
   from .base_provider import BaseProvider
   
   class NewProvider(BaseProvider):
       """Provider for New AI Service."""
       
       def __init__(self, api_key: Optional[str] = None):
           super().__init__()
           self.api_key = api_key
       
       async def generate(self, prompt: str, **kwargs) -> str:
           # Implementation
           pass
   ```

2. **Register Provider**:
   ```python
   # src/omnidev/models/providers/__init__.py
   from .new_provider import NewProvider
   
   PROVIDERS = {
       "new-provider": NewProvider,
       # ... other providers
   }
   ```

3. **Add Tests**:
   ```python
   # tests/unit/models/providers/test_new_provider.py
   def test_new_provider_generate():
       # Test implementation
       pass
   ```

4. **Update Documentation**:
   - Add to supported providers list
   - Document configuration
   - Add examples

### Adding a New Mode

1. **Create Mode Class**:
   ```python
   # src/omnidev/modes/new_mode.py
   from .base_mode import BaseMode
   
   class NewMode(BaseMode):
       """New operational mode."""
       
       async def execute(self, request: str) -> dict:
           # Implementation
           pass
   ```

2. **Register Mode**:
   ```python
   # src/omnidev/modes/__init__.py
   from .new_mode import NewMode
   
   MODES = {
       "new-mode": NewMode,
       # ... other modes
   }
   ```

3. **Add CLI Command**:
   ```python
   # src/omnidev/cli/commands.py
   @click.command()
   @click.option("--mode", "new-mode", ...)
   def new_mode_command(...):
       # Implementation
       pass
   ```

---

## Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Unit tests (fast, isolated)
├── integration/       # Integration tests (slower, with dependencies)
└── e2e/              # End-to-end tests (slowest, full system)
```

### Writing Tests

**Unit Tests**:
- Test individual functions/methods
- Mock external dependencies
- Fast execution (< 1 second each)
- High coverage (> 90%)

**Example**:
```python
import pytest
from omnidev.core.router import ModelRouter

def test_model_router_selects_simple_model():
    router = ModelRouter()
    task = {"complexity": 20, "type": "bug_fix"}
    model = router.select_model(task)
    assert model == "gpt-4o-mini"
```

**Integration Tests**:
- Test component interactions
- Use real dependencies (where safe)
- Test error scenarios
- Moderate execution time

**Example**:
```python
@pytest.mark.asyncio
async def test_file_operations_with_git():
    # Test file creation with Git integration
    pass
```

**E2E Tests**:
- Test complete workflows
- Use real providers (with mocks for API calls)
- Test user scenarios
- Can be slower

**Example**:
```python
@pytest.mark.e2e
async def test_agent_mode_complete_workflow():
    # Test full agent mode workflow
    pass
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/omnidev --cov-report=html

# Run specific test file
pytest tests/unit/test_router.py

# Run specific test
pytest tests/unit/test_router.py::test_model_router_selects_simple_model

# Run with verbose output
pytest -v

# Run only fast tests
pytest -m "not slow"
```

### Test Coverage

- **Target**: > 80% overall coverage
- **Critical paths**: > 95% coverage
- **New code**: 100% coverage required

### Mocking

Use `pytest-mock` for mocking:

```python
def test_with_mock(mocker):
    mock_provider = mocker.patch("omnidev.models.providers.OpenAIProvider")
    # Test with mock
    pass
```

---

## Documentation Standards

### Code Documentation

**Docstrings**: Use Google style

```python
def process_request(
    request: str,
    context: Optional[dict] = None,
) -> dict:
    """
    Process a user request and return results.
    
    This function analyzes the request, selects appropriate
    model, and executes the task.
    
    Args:
        request: User's natural language request
        context: Optional context dictionary
        
    Returns:
        Dictionary containing:
            - result: Generated code or response
            - model: Model used
            - tokens: Token usage
            - cost: Estimated cost
            
    Raises:
        ProviderError: If no provider is available
        ValidationError: If request is invalid
        
    Example:
        >>> result = process_request("Create a FastAPI endpoint")
        >>> print(result["result"])
    """
    pass
```

### API Documentation

- Document all public functions/classes
- Include examples
- Document parameters and return types
- Document exceptions
- Keep docs up-to-date with code

### User Documentation

- Clear installation instructions
- Usage examples
- Configuration guide
- Troubleshooting section
- FAQ

### Architecture Documentation

- System architecture diagrams
- Component interactions
- Data flow
- Design decisions and rationale

---

## Git Workflow

### Branch Strategy

- **main**: Production-ready code
- **develop**: Integration branch
- **feature/**: New features
- **bugfix/**: Bug fixes
- **hotfix/**: Critical fixes

### Commit Messages

Follow **Conventional Commits**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

**Example**:
```
feat(context): Add automatic file relevance scoring

Implement intelligent file selection based on:
- Import dependencies
- Recent edit history
- User focus patterns

Closes #123
```

### Pull Request Process

1. **Create PR**:
   - Clear title and description
   - Reference related issues
   - Add screenshots/examples if applicable

2. **PR Checklist**:
   - [ ] Code follows style guide
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] All tests passing
   - [ ] No linting errors
   - [ ] Type checking passes

3. **Review Process**:
   - At least one approval required
   - Address all review comments
   - Keep PR focused (one feature/fix)

4. **Merge**:
   - Squash commits (if requested)
   - Delete branch after merge
   - Update CHANGELOG.md

---

## Release Process

### Versioning

Follow **Semantic Versioning** (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

1. **Prepare Release**:
   - [ ] Update version in `pyproject.toml`
   - [ ] Update CHANGELOG.md
   - [ ] Update documentation
   - [ ] Run full test suite
   - [ ] Check for security vulnerabilities

2. **Create Release**:
   - [ ] Create git tag: `v1.0.0`
   - [ ] Push tag to GitHub
   - [ ] Create GitHub release
   - [ ] Publish to PyPI (if applicable)

3. **Post-Release**:
   - [ ] Announce release
   - [ ] Update roadmap
   - [ ] Monitor for issues

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pre-commit install
```

Hooks run:
- Black (formatting)
- Ruff (linting)
- mypy (type checking)
- Tests (quick check)

---

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure you're in virtual environment
source venv/bin/activate

# Reinstall in development mode
pip install -e .
```

**Test Failures**:
```bash
# Clear pytest cache
pytest --cache-clear

# Run with verbose output
pytest -vv
```

**Type Checking Errors**:
```bash
# Check specific file
mypy src/omnidev/path/to/file.py

# Ignore specific errors (temporary)
# type: ignore
```

---

## Getting Help

- **GitHub Issues**: Report bugs, request features
- **Discussions**: Ask questions, share ideas
- **Discord**: Real-time chat (coming soon)
- **Documentation**: Check docs/ directory

---

## Code of Conduct

We follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Be respectful, inclusive, and professional.

---

**Happy coding! 🚀**

