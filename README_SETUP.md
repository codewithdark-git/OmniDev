# OmniDev - Setup Guide

This guide will help you set up the OmniDev development environment using Miniconda and UV package manager.

## Prerequisites

- **Miniconda** (or Anaconda) installed on your system
  - Download from: https://docs.conda.io/en/latest/miniconda.html
- **Git** installed
- **Internet connection** for downloading packages

## Quick Setup

### Windows (PowerShell)

```powershell
# Run the setup script
.\setup_environment.ps1
```

### Linux/macOS (Bash)

```bash
# Make the script executable
chmod +x setup_environment.sh

# Run the setup script
./setup_environment.sh
```

## Manual Setup

If you prefer to set up manually:

### 1. Create Conda Environment

```bash
# Create environment with Python 3.10
conda create -n omnidev python=3.10 -y

# Activate the environment
conda activate omnidev
```

### 2. Install UV Package Manager

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Or using pip:**
```bash
pip install uv
```

### 3. Install Project Dependencies

```bash
# Install the project in development mode with all dependencies
uv pip install -e ".[dev]"
```

### 4. Configure AI Provider

OmniDev supports multiple AI providers. The recommended free option is **Groq**:

```bash
# Start interactive mode and run setup
omnidev -i
# Then type: /setup

# Or run the setup wizard directly
omnidev --setup
```

**Supported Providers:**
| Provider | Free Tier | Get API Key |
|----------|-----------|-------------|
| **Groq** | ✅ 30 req/min | [console.groq.com](https://console.groq.com) |
| OpenAI | ❌ | [platform.openai.com](https://platform.openai.com/api-keys) |
| Anthropic | ❌ | [console.anthropic.com](https://console.anthropic.com) |
| Google | ❌ | [aistudio.google.com](https://aistudio.google.com/apikey) |
| OpenRouter | ❌ | [openrouter.ai/keys](https://openrouter.ai/keys) |

**Manual Configuration:**
```bash
# Create .env file in project root
echo "GROQ_API_KEY=your-key-here" > .env

# Or for other providers:
echo "OPENAI_API_KEY=your-key-here" > .env
```

**Important:** Add `.env` to your `.gitignore` to keep your API keys secure.

### 5. Verify Installation

```bash
# Check if OmniDev is installed
omnidev --version

# Verify OpenRouter API key is configured
omnidev config list-keys

# Or test Python import
python -c "import omnidev; print('✅ Installation successful')"
```

## Using the Environment

### Activate Environment

```bash
conda activate omnidev
```

### Using OmniDev

```bash
# Start interactive mode (recommended)
omnidev -i

# Run a single query
omnidev "create a Python function to parse JSON"

# Run with specific mode
omnidev --mode agent "add authentication to the API"

# View available slash commands in interactive mode
/help
```

### Deactivate Environment

```bash
conda deactivate
```

### Update Dependencies

```bash
# Update all dependencies
uv pip install --upgrade -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=omnidev --cov-report=html
```

### Format Code

```bash
# Format with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/
```

## Troubleshooting

### UV Not Found

If `uv` command is not found after installation:

**Linux/macOS:**
```bash
export PATH="$HOME/.cargo/bin:$PATH"
# Add to ~/.bashrc or ~/.zshrc for persistence
```

**Windows:**
Add `%USERPROFILE%\.cargo\bin` to your PATH environment variable.

### Conda Environment Issues

If you have issues with the conda environment:

```bash
# Remove and recreate
conda deactivate
conda env remove -n omnidev
conda create -n omnidev python=3.10 -y
conda activate omnidev
```

### Import Errors

If you get import errors:

```bash
# Reinstall in development mode
uv pip install -e ".[dev]" --force-reinstall
```

## OpenRouter API Key Setup

After installation, you need to configure the OpenRouter API key for agent operations:

### Quick Setup
```bash
omnidev setup
```

This interactive wizard will:
1. Prompt for your OpenRouter API key
2. Ask where to store it (project `.env` file or system keyring)
3. Verify the key is saved correctly

### Manual Setup

**Option 1: Project .env file (Recommended)**
```bash
# Create .env file in project root
cat > .env << EOF
OMNIDEV_OPENROUTER_API_KEY=your-api-key-here
EOF

# Add to .gitignore
echo ".env" >> .gitignore
```

**Option 2: System Keyring**
```bash
omnidev config add-key openrouter your-api-key-here
```

**Option 3: Environment Variable**
```bash
# Linux/macOS
export OMNIDEV_OPENROUTER_API_KEY=your-api-key-here

# Windows PowerShell
$env:OMNIDEV_OPENROUTER_API_KEY="your-api-key-here"
```

For detailed information, see [SETUP_OPENROUTER.md](SETUP_OPENROUTER.md).

## Next Steps

After setup, you can:

1. Read [DEVELOPMENT.md](DEVELOPMENT.md) for development guidelines
2. Read [AGENTS.md](AGENTS.md) for code contribution best practices
3. Read [FEATURES.md](FEATURES.md) to understand the project features
4. Read [SETUP_OPENROUTER.md](SETUP_OPENROUTER.md) for OpenRouter API key configuration
5. Start contributing to the codebase!

## Need Help?

- Check [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development instructions
- Open an issue on GitHub
- Join our community discussions

