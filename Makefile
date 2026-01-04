.PHONY: help install install-dev test lint format type-check clean setup

help:
	@echo "OmniDev Development Commands"
	@echo ""
	@echo "  make setup          - Set up development environment"
	@echo "  make install        - Install package in development mode"
	@echo "  make install-dev    - Install with development dependencies"
	@echo "  make test           - Run tests"
	@echo "  make test-cov       - Run tests with coverage"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make type-check     - Run type checker"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make all            - Run format, lint, type-check, and test"

setup:
	@echo "Setting up development environment..."
	@if [ -f setup_environment.sh ]; then \
		bash setup_environment.sh; \
	elif [ -f setup_environment.ps1 ]; then \
		powershell -ExecutionPolicy ByPass -File setup_environment.ps1; \
	else \
		echo "Please run setup script manually"; \
	fi

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

test:
	pytest

test-cov:
	pytest --cov=omnidev --cov-report=html --cov-report=term-missing

lint:
	ruff check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

type-check:
	mypy src/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

all: format lint type-check test
	@echo "All checks passed!"

