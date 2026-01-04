# OpenRouter API Key Setup Guide

## Overview

OmniDev uses OpenRouter API keys **exclusively for agent operations** (internal orchestration, decision-making, planning, validation). The OpenRouter API is **NOT used** for code generation or user-facing text generation.

## Quick Setup

Run the setup wizard:

```bash
omnidev setup
```

This interactive wizard will:
1. Prompt you for your OpenRouter API key
2. Ask where to store it (project .env file or system keyring)
3. Save the key and verify it's accessible

## Manual Setup

### Option 1: Project .env File (Recommended)

Create a `.env` file in your project root:

```bash
# .env
OMNIDEV_OPENROUTER_API_KEY=your-api-key-here
```

**Important:** Add `.env` to your `.gitignore` to keep your API key secure.

### Option 2: Environment Variable

Set the environment variable:

```bash
# Linux/macOS
export OMNIDEV_OPENROUTER_API_KEY=your-api-key-here

# Windows PowerShell
$env:OMNIDEV_OPENROUTER_API_KEY="your-api-key-here"

# Windows CMD
set OMNIDEV_OPENROUTER_API_KEY=your-api-key-here
```

### Option 3: System Keyring (Secure)

Use the CLI command:

```bash
omnidev config add-key openrouter your-api-key-here
```

This stores the key securely in your system's keyring.

## Variable Names

The codebase uses these environment variable names (checked in order):

1. `OMNIDEV_OPENROUTER_API_KEY` (preferred)
2. `OPENROUTER_API_KEY` (fallback for backward compatibility)

## Verification

Check if your API key is configured:

```bash
omnidev config list-keys
```

## Getting Your API Key

1. Visit [OpenRouter.ai](https://openrouter.ai)
2. Sign up or log in
3. Go to [API Keys](https://openrouter.ai/keys)
4. Create a new API key
5. Copy the key and use it in the setup wizard

## Project-Specific Configuration

Each project can have its own `.env` file with a different OpenRouter API key. This allows you to:
- Use different API keys for different projects
- Keep keys isolated per project
- Easily share project setup without exposing keys (via .gitignore)

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Add `.env` to `.gitignore`** in every project
3. **Use project-specific keys** when possible
4. **Rotate keys regularly** if exposed
5. **Use system keyring** for maximum security (Option 3)

## Troubleshooting

### API Key Not Found

If agents fail with "OpenRouter API key not configured":

1. Verify the key is set: `omnidev config list-keys`
2. Check the `.env` file exists and contains `OMNIDEV_OPENROUTER_API_KEY`
3. Ensure you're in the correct project directory
4. Try reloading: `source .env` (Linux/macOS) or restart your terminal

### Key Stored but Not Accessible

1. Check file permissions on `.env`
2. Verify the variable name matches exactly: `OMNIDEV_OPENROUTER_API_KEY`
3. Ensure no extra spaces or quotes in the `.env` file
4. Try using the setup wizard again to regenerate

## Usage in Code

The API key is automatically loaded by `ConfigManager`:

```python
from omnidev.core.config import ConfigManager

config = ConfigManager(project_root)
api_key = config.get_api_key("openrouter")  # Automatically loads from .env
```

The key lookup order:
1. Environment variables (`OMNIDEV_OPENROUTER_API_KEY`)
2. Project `.env` file
3. System keyring

