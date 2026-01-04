#!/usr/bin/env python3
"""
Verification script for OmniDev setup.

This script checks that the development environment is set up correctly.
"""

import sys
from pathlib import Path


def check_python_version() -> bool:
    """Check if Python version is 3.10 or higher."""
    if sys.version_info < (3, 10):
        print(f"❌ Python 3.10+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def check_package_imports() -> bool:
    """Check if required packages can be imported."""
    try:
        import click
        import rich
        print("✅ Core dependencies (click, rich) available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False


def check_omnidev_import() -> bool:
    """Check if OmniDev package can be imported."""
    try:
        import omnidev
        print(f"✅ OmniDev package imported (version: {omnidev.__version__})")
        return True
    except ImportError as e:
        print(f"❌ Cannot import OmniDev: {e}")
        print("   Try running: uv pip install -e '.[dev]'")
        return False


def check_cli_command() -> bool:
    """Check if CLI command works."""
    try:
        from omnidev.cli.main import main
        print("✅ CLI module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Cannot import CLI: {e}")
        return False


def check_project_structure() -> bool:
    """Check if project structure is correct."""
    required_dirs = [
        "src/omnidev",
        "src/omnidev/cli",
        "src/omnidev/core",
        "src/omnidev/modes",
        "src/omnidev/models",
        "src/omnidev/context",
        "src/omnidev/actions",
        "src/omnidev/tools",
        "src/omnidev/utils",
        "tests",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"❌ Missing directory: {dir_path}")
            all_exist = False
    
    if all_exist:
        print("✅ Project structure is correct")
    
    return all_exist


def main() -> int:
    """Run all verification checks."""
    print("🔍 Verifying OmniDev setup...\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Project Structure", check_project_structure),
        ("Package Imports", check_package_imports),
        ("OmniDev Import", check_omnidev_import),
        ("CLI Command", check_cli_command),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"Checking {name}...", end=" ")
        result = check_func()
        results.append(result)
        print()
    
    print("\n" + "=" * 50)
    if all(results):
        print("✅ All checks passed! Setup is complete.")
        print("\nNext steps:")
        print("  - Read DEVELOPMENT.md for development guidelines")
        print("  - Read AGENTS.md for code contribution best practices")
        print("  - Run 'pytest' to run the test suite")
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.")
        print("\nTo fix issues:")
        print("  - Run the setup script: ./setup_environment.sh (Linux/macOS)")
        print("  - Or: .\\setup_environment.ps1 (Windows)")
        print("  - Or manually: uv pip install -e '.[dev]'")
        return 1


if __name__ == "__main__":
    sys.exit(main())

